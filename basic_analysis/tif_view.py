# -*- coding: utf-8 -*-
"""
PyQt5 TIFF Player

Changes:
- Preview (first 1000 frames) is ON by default.
- Start + Span loading (start, start+span, ...). Options only used when loading.
- Clipping percentiles controls (low/high). Button to apply to current data.
- Buttons to apply Temporal Moving Average and Gaussian Spatial Filter to data after load.
- Load does NOT auto-apply temporal average or gaussian filter. Percentiles are used once at load
  to initialize min/max clipping; you can re-apply with the button after adjusting values.

Original functionality preserved: play/stop, FPS, frame scrollbar, min/max clipping sliders,
side-by-side current/average frames, resizing with aspect ratio, and loading dialog.
"""

import sys
import os
import math
from typing import Optional

import numpy as np
from PIL import Image, ImageSequence
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFileDialog, QCheckBox, QSpinBox, QDoubleSpinBox, QProgressDialog, QMessageBox
)

# ---------- Optional SciPy acceleration for Gaussian filtering ----------
try:
    from scipy.ndimage import gaussian_filter as _scipy_gaussian_filter
    _SCIPY_AVAILABLE = True
except Exception:
    _SCIPY_AVAILABLE = False


def _moving_average_stack_trailing(stack: np.ndarray, window: int) -> np.ndarray:
    """
    Trailing moving average over time axis (axis=0). Length preserved.
    stack: (T, H, W[,...]) -> float64
    """
    if window <= 1 or stack.shape[0] <= 1:
        return stack
    T = stack.shape[0]
    csum = np.cumsum(stack, axis=0, dtype=np.float64)
    out = np.empty_like(stack, dtype=np.float64)
    for i in range(T):
        j0 = max(0, i - window + 1)
        if j0 == 0:
            s = csum[i]
        else:
            s = csum[i] - csum[j0 - 1]
        n = i - j0 + 1
        out[i] = s / float(n)
    return out


def _gaussian_kernel1d(sigma: float, radius: Optional[int] = None) -> np.ndarray:
    if sigma <= 0:
        return np.array([1.0], dtype=np.float64)
    if radius is None:
        radius = max(1, int(math.ceil(3.0 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    k = np.exp(-(x * x) / (2.0 * sigma * sigma))
    k /= k.sum()
    return k


def _convolve1d_reflect(a: np.ndarray, k: np.ndarray, axis: int) -> np.ndarray:
    """
    Separable 1D convolution along given axis with reflect padding.
    a: ndarray (...), k: 1D kernel
    """
    if k.size == 1:
        return a
    radius = (k.size - 1) // 2
    pad_width = [(0, 0)] * a.ndim
    pad_width[axis] = (radius, radius)
    ap = np.pad(a, pad_width, mode='reflect')
    ap = np.moveaxis(ap, axis, 0)

    flat_ap = ap.reshape((ap.shape[0], -1))
    str0, str1 = flat_ap.strides
    n_out = flat_ap.shape[0] - 2 * radius
    win_shape = (n_out, k.size, flat_ap.shape[1])
    win_strides = (str0, str0, str1)
    windows = np.lib.stride_tricks.as_strided(flat_ap, shape=win_shape, strides=win_strides)
    flat_out = np.tensordot(windows, k, axes=([1], [0]))  # (n_out, cols)
    out = flat_out.reshape((n_out,) + ap.shape[1:])
    return np.moveaxis(out, 0, axis)


def _gaussian_blur_stack_np(stack: np.ndarray, sigma: float) -> np.ndarray:
    """
    Apply 2D Gaussian blur (spatial only) to each frame in stack using separable conv.
    stack: (T, H, W) or (T, H, W, C)
    """
    if sigma <= 0:
        return stack
    k = _gaussian_kernel1d(sigma)
    out = _convolve1d_reflect(stack, k, axis=1)  # Y
    out = _convolve1d_reflect(out, k, axis=2)    # X
    return out


class TiffPlayerQt(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TIFF Player (PyQt5)")

        # State
        self.running = False
        self.tiff_images = []          # list of frames (np.ndarray, float32/float64)
        self.current_frame = 0
        self.fps = 10
        self.min_clip = -65536
        self.max_clip = 65536
        self.average_frame = None
        self.loaded_path = None

        # Timer for playback
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance_frame)

        # UI
        self._build_ui()
        self._wire_events()
        self.setMinimumSize(1150, 780)

    # ---------------------- UI ----------------------
    def _build_ui(self):
        root = QGridLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Left/Right image views
        self.left_label = QLabel()
        self.left_label.setObjectName("leftView")
        self.left_label.setAlignment(Qt.AlignCenter)
        self.left_label.setStyleSheet("QLabel#leftView { background: black; }")

        self.right_label = QLabel()
        self.right_label.setObjectName("rightView")
        self.right_label.setStyleSheet("QLabel#rightView { background: black; }")
        self.right_label.setAlignment(Qt.AlignCenter)

        root.addWidget(self.left_label, 0, 0)
        root.addWidget(self.right_label, 0, 1)

        # Row 1: Load controls
        top = QHBoxLayout()
        self.btn_open = QPushButton("Open TIFF")
        self.btn_play = QPushButton("Play")
        self.btn_stop = QPushButton("Stop")
        self.btn_play.setEnabled(False)
        self.btn_stop.setEnabled(False)

        top.addWidget(self.btn_open)
        top.addWidget(self.btn_play)
        top.addWidget(self.btn_stop)

        top.addSpacing(16)
        top.addWidget(QLabel("FPS:"))
        self.sld_fps = QSlider(Qt.Horizontal)
        self.sld_fps.setRange(1, 60)
        self.sld_fps.setValue(self.fps)
        self.sld_fps.setSingleStep(1)
        self.sld_fps.setPageStep(5)
        self.lbl_fps_val = QLabel(str(self.fps))
        top.addWidget(self.sld_fps, stretch=1)
        top.addWidget(self.lbl_fps_val)

        top.addSpacing(16)
        self.chk_preview = QCheckBox("Preview (first 1000 frames)")
        self.chk_preview.setChecked(True)  # default ON
        top.addWidget(self.chk_preview)

        top.addSpacing(16)
        top.addWidget(QLabel("Start:"))
        self.spin_start = QSpinBox()
        self.spin_start.setRange(0, 2_000_000_000)
        self.spin_start.setValue(0)
        top.addWidget(self.spin_start)

        top.addSpacing(12)
        top.addWidget(QLabel("Span:"))
        self.spin_span = QSpinBox()
        self.spin_span.setRange(1, 2_000_000_000)
        self.spin_span.setValue(1)
        top.addWidget(self.spin_span)

        row1 = QWidget()
        row1.setLayout(top)
        root.addWidget(row1, 1, 0, 1, 2)

        # Row 2: Display/Processing controls (applied via buttons after load)
        opts = QHBoxLayout()

        # Clipping percentiles
        opts.addWidget(QLabel("Clip % Low:"))
        self.spin_clip_lo = QDoubleSpinBox()
        self.spin_clip_lo.setRange(0.0, 100.0)
        self.spin_clip_lo.setDecimals(1)
        self.spin_clip_lo.setSingleStep(0.5)
        self.spin_clip_lo.setValue(5.0)
        self.spin_clip_lo.setToolTip("Lower percentile for display clipping.")
        opts.addWidget(self.spin_clip_lo)

        opts.addSpacing(8)
        opts.addWidget(QLabel("High:"))
        self.spin_clip_hi = QDoubleSpinBox()
        self.spin_clip_hi.setRange(0.0, 100.0)
        self.spin_clip_hi.setDecimals(1)
        self.spin_clip_hi.setSingleStep(0.5)
        self.spin_clip_hi.setValue(95.0)
        self.spin_clip_hi.setToolTip("Upper percentile for display clipping.")
        opts.addWidget(self.spin_clip_hi)

        self.btn_apply_clip = QPushButton("Apply Clip %")
        self.btn_apply_clip.setToolTip("Recompute min/max clip from percentiles over current data.")
        opts.addWidget(self.btn_apply_clip)

        # Temporal moving average
        opts.addSpacing(20)
        opts.addWidget(QLabel("Temporal avg window:"))
        self.spin_tavg = QSpinBox()
        self.spin_tavg.setRange(1, 1_000_000)
        self.spin_tavg.setValue(1)
        self.spin_tavg.setToolTip("Trailing moving average window (frames).")
        opts.addWidget(self.spin_tavg)

        self.btn_apply_tavg = QPushButton("Apply Temporal Avg")
        self.btn_apply_tavg.setToolTip("Apply trailing moving average to data in memory.")
        opts.addWidget(self.btn_apply_tavg)

        # Gaussian spatial filter
        opts.addSpacing(20)
        opts.addWidget(QLabel("Gaussian sigma:"))
        self.spin_sigma = QDoubleSpinBox()
        self.spin_sigma.setRange(0.0, 1000.0)
        self.spin_sigma.setDecimals(2)
        self.spin_sigma.setSingleStep(0.1)
        self.spin_sigma.setValue(0.0)
        self.spin_sigma.setToolTip("Spatial Gaussian blur sigma (pixels).")
        opts.addWidget(self.spin_sigma)

        self.btn_apply_gauss = QPushButton("Apply Gaussian")
        self.btn_apply_gauss.setToolTip("Apply spatial Gaussian blur to data in memory.")
        opts.addWidget(self.btn_apply_gauss)

        row2 = QWidget()
        row2.setLayout(opts)
        root.addWidget(row2, 2, 0, 1, 2)

        # Frame scrollbar
        self.sld_frame = QSlider(Qt.Horizontal)
        self.sld_frame.setRange(0, 0)
        self.sld_frame.setEnabled(False)
        root.addWidget(self.sld_frame, 3, 0, 1, 2)

        # Clip sliders (interactive at display time)
        clip_layout = QHBoxLayout()
        clip_layout.addWidget(QLabel("Min Clip:"))
        self.sld_min = QSlider(Qt.Horizontal)
        self.sld_min.setRange(-65536, 65536)
        self.sld_min.setValue(self.min_clip)
        self.sld_min.setSingleStep(100)
        self.sld_min.setPageStep(1000)
        self.lbl_min_val = QLabel(str(self.min_clip))
        clip_layout.addWidget(self.sld_min, stretch=1)
        clip_layout.addWidget(self.lbl_min_val)

        clip_layout.addSpacing(12)
        clip_layout.addWidget(QLabel("Max Clip:"))
        self.sld_max = QSlider(Qt.Horizontal)
        self.sld_max.setRange(-65536, 65536)
        self.sld_max.setValue(self.max_clip)
        self.sld_max.setSingleStep(100)
        self.sld_max.setPageStep(1000)
        self.lbl_max_val = QLabel(str(self.max_clip))
        clip_layout.addWidget(self.sld_max, stretch=1)
        clip_layout.addWidget(self.lbl_max_val)

        clip_row = QWidget()
        clip_row.setLayout(clip_layout)
        root.addWidget(clip_row, 4, 0, 1, 2)

        # Status
        status_layout = QHBoxLayout()
        self.lbl_status = QLabel("No file loaded.")
        status_layout.addWidget(self.lbl_status)
        status_row = QWidget()
        status_row.setLayout(status_layout)
        root.addWidget(status_row, 5, 0, 1, 2)

        root.setRowStretch(0, 1)
        root.setColumnStretch(0, 1)
        root.setColumnStretch(1, 1)

    def _wire_events(self):
        self.btn_open.clicked.connect(self._open_tiff)
        self.btn_play.clicked.connect(self.play_movie)
        self.btn_stop.clicked.connect(self.stop_movie)

        self.sld_fps.valueChanged.connect(self._on_fps_changed)
        self.sld_frame.valueChanged.connect(self._on_scroll_frame)

        self.sld_min.valueChanged.connect(self._on_min_clip_changed)
        self.sld_max.valueChanged.connect(self._on_max_clip_changed)

        # Post-load processing buttons
        self.btn_apply_clip.clicked.connect(self._apply_clip_percentiles_to_data)
        self.btn_apply_tavg.clicked.connect(self._apply_temporal_avg_to_data)
        self.btn_apply_gauss.clicked.connect(self._apply_gaussian_to_data)

        # No auto-reload on option changes; applied only when loading or pressing buttons.

    # ---------------------- Core Logic ----------------------
    def _open_tiff(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open TIFF", "", "TIFF Files (*.tif *.tiff)"
        )
        if not path:
            return
        self.loaded_path = path
        self._load_tiff(path)

    def _load_tiff(self, path: str):
        preview = self.chk_preview.isChecked()
        span = max(1, int(self.spin_span.value()))
        start = max(0, int(self.spin_start.value()))

        # Percentiles for initial clip
        clip_lo = float(self.spin_clip_lo.value())
        clip_hi = float(self.spin_clip_hi.value())
        if clip_lo > clip_hi:
            clip_lo, clip_hi = clip_hi, clip_lo

        try:
            img = Image.open(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")
            return

        # Count frames
        try:
            total_frames = getattr(img, "n_frames", None)
            if total_frames is None:
                total_frames = sum(1 for _ in ImageSequence.Iterator(img))
        except Exception:
            total_frames = 1

        # Apply preview cap
        effective_total = min(1000, total_frames) if preview else total_frames
        if effective_total <= 0:
            QMessageBox.warning(self, "Warning", "No frames available.")
            return

        # Clamp start after preview cap
        if start >= effective_total:
            start = max(0, effective_total - 1)
            self.spin_start.blockSignals(True)
            self.spin_start.setValue(start)
            self.spin_start.blockSignals(False)

        # Build indices using start and span
        indices = list(range(start, effective_total, span))
        if not indices:
            indices = [start]

        progress = QProgressDialog("Loading TIFF file...", "Cancel", 0, len(indices), self)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        frames = []
        cancelled = False

        try:
            for i, frame_idx in enumerate(indices):
                if progress.wasCanceled():
                    cancelled = True
                    break
                try:
                    img.seek(frame_idx)
                    arr = np.array(img, dtype=np.float32)  # float for processing/display
                    frames.append(arr)
                except Exception as fe:
                    print(f"Warning: could not read frame {frame_idx}: {fe}")
                progress.setValue(i + 1)
                QApplication.processEvents()
        finally:
            progress.reset()

        if cancelled or len(frames) == 0:
            self.tiff_images = []
            self.average_frame = None
            self.sld_frame.setEnabled(False)
            self.btn_play.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self._clear_views()
            self.lbl_status.setText("Loading canceled or no readable frames.")
            return

        # Store frames (no temporal/gaussian filtering at load)
        stack = np.stack(frames, axis=0)
        self.tiff_images = [stack[i] for i in range(stack.shape[0])]

        # Average frame
        self.average_frame = np.mean(stack, axis=0)

        # Initial clipping from percentiles on loaded data
        try:
            self.min_clip = int(np.percentile(stack, clip_lo))
            self.max_clip = int(np.percentile(stack, clip_hi))
        except Exception as e:
            print(f"Warning: percentile computation failed: {e}")
            self.min_clip, self.max_clip = -65536, 65536
        self._apply_new_clip_values()

        # Frame scrollbar
        self.sld_frame.blockSignals(True)
        self.sld_frame.setRange(0, len(self.tiff_images) - 1)
        self.sld_frame.setValue(0)
        self.sld_frame.setEnabled(True)
        self.sld_frame.blockSignals(False)

        self.current_frame = 0
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)

        # Initial display
        self._display_frame(self.current_frame)
        self._display_average_frame()

        # Status
        h, w = self.tiff_images[0].shape[:2]
        loaded_count = len(self.tiff_images)
        opt_info = f"preview={'on' if preview else 'off'}, start={start}, span={span}"
        clip_info = f"clip[{self.min_clip}, {self.max_clip}] from %[{clip_lo:.1f},{clip_hi:.1f}]"
        self.lbl_status.setText(
            f"Loaded {loaded_count}/{effective_total} frames from: {os.path.basename(path)} "
            f"({w}x{h}); {clip_info}; {opt_info}"
        )

    # ---- Post-load operations ----
    def _apply_clip_percentiles_to_data(self):
        if not self.tiff_images:
            return
        clip_lo = float(self.spin_clip_lo.value())
        clip_hi = float(self.spin_clip_hi.value())
        if clip_lo > clip_hi:
            clip_lo, clip_hi = clip_hi, clip_lo
        stack = np.stack(self.tiff_images, axis=0)
        try:
            self.min_clip = int(np.percentile(stack, clip_lo))
            self.max_clip = int(np.percentile(stack, clip_hi))
        except Exception as e:
            print(f"Warning: percentile computation failed: {e}")
            return
        self._apply_new_clip_values()
        self._display_frame(self.current_frame)
        self._display_average_frame()

    def _apply_temporal_avg_to_data(self):
        if not self.tiff_images:
            return
        window = max(1, int(self.spin_tavg.value()))
        if window <= 1:
            return
        stack = np.stack(self.tiff_images, axis=0).astype(np.float64, copy=False)
        stack = _moving_average_stack_trailing(stack, window)
        self.tiff_images = [stack[i] for i in range(stack.shape[0])]
        self.average_frame = np.mean(stack, axis=0)
        self._display_frame(self.current_frame)
        self._display_average_frame()
        # keep clip unchanged; user can press Apply Clip % to recompute if desired

    def _apply_gaussian_to_data(self):
        if not self.tiff_images:
            return
        sigma = float(self.spin_sigma.value())
        if sigma <= 0.0:
            return
        stack = np.stack(self.tiff_images, axis=0).astype(np.float64, copy=False)
        if _SCIPY_AVAILABLE:
            stack = _scipy_gaussian_filter(stack, sigma=(0.0, sigma, sigma), mode='nearest')
        else:
            stack = _gaussian_blur_stack_np(stack, sigma)
        self.tiff_images = [stack[i] for i in range(stack.shape[0])]
        self.average_frame = np.mean(stack, axis=0)
        self._display_frame(self.current_frame)
        self._display_average_frame()
        # keep clip unchanged; user can press Apply Clip % to recompute if desired

    def _apply_new_clip_values(self):
        self.sld_min.blockSignals(True)
        self.sld_max.blockSignals(True)

        minv = int(np.clip(self.min_clip, -65536, 65536))
        maxv = int(np.clip(self.max_clip, -65536, 65536))
        if minv > maxv:
            minv, maxv = maxv, minv

        self.min_clip, self.max_clip = minv, maxv
        self.sld_min.setValue(minv)
        self.sld_max.setValue(maxv)
        self.lbl_min_val.setText(str(minv))
        self.lbl_max_val.setText(str(maxv))

        self.sld_min.blockSignals(False)
        self.sld_max.blockSignals(False)

    # ---------------------- Playback ----------------------
    def play_movie(self):
        if not self.tiff_images:
            return
        self.running = True
        self.btn_play.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._update_timer_interval()
        self.timer.start()

    def stop_movie(self):
        self.running = False
        self.timer.stop()
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _advance_frame(self):
        if not self.tiff_images:
            return
        self._validate_frame_index()
        self._display_frame(self.current_frame)
        self.current_frame = (self.current_frame + 1) % len(self.tiff_images)
        self.sld_frame.blockSignals(True)
        self.sld_frame.setValue(self.current_frame)
        self.sld_frame.blockSignals(False)

    def _update_timer_interval(self):
        self.timer.setInterval(int(1000 / max(1, self.fps)))

    # ---------------------- Display ----------------------
    def _validate_frame_index(self):
        if not self.tiff_images:
            self.current_frame = 0
        else:
            self.current_frame = max(0, min(self.current_frame, len(self.tiff_images) - 1))

    def _apply_clipping(self, frame: np.ndarray) -> np.ndarray:
        if self.max_clip == self.min_clip:
            return np.zeros_like(frame, dtype=np.uint8)
        frame = np.clip(frame, self.min_clip, self.max_clip)
        frame = ((frame - self.min_clip) / float(self.max_clip - self.min_clip) * 255.0).astype(np.uint8)
        return frame

    def _np_to_qpixmap(self, arr_uint8: np.ndarray) -> QPixmap:
        """
        Convert NumPy array to QPixmap. Use QImage.copy() to detach from the NumPy buffer.
        """
        arr = np.ascontiguousarray(arr_uint8)

        if arr.ndim == 2:
            h, w = arr.shape
            bytes_per_line = w
            qimg = QImage(arr.data, w, h, bytes_per_line, QImage.Format_Grayscale8).copy()
            return QPixmap.fromImage(qimg)

        if arr.ndim == 3:
            h, w, c = arr.shape
            if c == 3:
                bytes_per_line = 3 * w
                qimg = QImage(arr.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                return QPixmap.fromImage(qimg)
            elif c == 4:
                bytes_per_line = 4 * w
                qimg = QImage(arr.data, w, h, bytes_per_line, QImage.Format_RGBA8888).copy()
                return QPixmap.fromImage(qimg)
            else:
                gray = np.ascontiguousarray(arr[..., 0])
                h, w = gray.shape
                qimg = QImage(gray.data, w, h, w, QImage.Format_Grayscale8).copy()
                return QPixmap.fromImage(qimg)

        gray = np.ascontiguousarray(np.squeeze(arr))
        if gray.ndim != 2:
            raise ValueError(f"Unsupported array shape for display: {arr.shape}")
        h, w = gray.shape
        qimg = QImage(gray.data, w, h, w, QImage.Format_Grayscale8).copy()
        return QPixmap.fromImage(qimg)

    def _scaled_for_label(self, pix: QPixmap, label: QLabel) -> QPixmap:
        target: QSize = label.size()
        if target.width() < 2 or target.height() < 2:
            return pix
        return pix.scaled(target, Qt.KeepAspectRatio, transformMode=Qt.FastTransformation)

    def _display_frame(self, frame_index: int):
        self._validate_frame_index()
        if not self.tiff_images:
            return
        frame = self.tiff_images[self.current_frame]
        frame = self._apply_clipping(frame)
        pix = self._np_to_qpixmap(frame)
        pix = self._scaled_for_label(pix, self.left_label)
        self.left_label.setPixmap(pix)

    def _display_average_frame(self):
        if self.average_frame is None:
            return
        avg = self._apply_clipping(self.average_frame)
        pix = self._np_to_qpixmap(avg)
        pix = self._scaled_for_label(pix, self.right_label)
        self.right_label.setPixmap(pix)

    def _clear_views(self):
        self.left_label.clear()
        self.right_label.clear()

    # ---------------------- Events ----------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.tiff_images:
            self._display_frame(self.current_frame)
        if self.average_frame is not None:
            self._display_average_frame()

    def closeEvent(self, event):
        self.stop_movie()
        super().closeEvent(event)

    # ---------------------- Handlers ----------------------
    def _on_fps_changed(self, value: int):
        self.fps = int(value)
        self.lbl_fps_val.setText(str(self.fps))
        if self.running:
            self._update_timer_interval()

    def _on_scroll_frame(self, value: int):
        self.current_frame = int(value)
        self._validate_frame_index()
        self._display_frame(self.current_frame)

    def _on_min_clip_changed(self, value: int):
        self.min_clip = int(value)
        self.lbl_min_val.setText(str(self.min_clip))
        if self.min_clip > self.max_clip:
            self.max_clip = self.min_clip
            self.sld_max.blockSignals(True)
            self.sld_max.setValue(self.max_clip)
            self.lbl_max_val.setText(str(self.max_clip))
            self.sld_max.blockSignals(False)
        self._validate_frame_index()
        self._display_frame(self.current_frame)
        self._display_average_frame()

    def _on_max_clip_changed(self, value: int):
        self.max_clip = int(value)
        self.lbl_max_val.setText(str(self.max_clip))
        if self.max_clip < self.min_clip:
            self.min_clip = self.max_clip
            self.sld_min.blockSignals(True)
            self.sld_min.setValue(self.min_clip)
            self.lbl_min_val.setText(str(self.min_clip))
            self.sld_min.blockSignals(False)
        self._validate_frame_index()
        self._display_frame(self.current_frame)
        self._display_average_frame()


def main():
    # Workaround for some XKB/compose issues in remote/WSL sessions
    if "QT_IM_MODULE" not in os.environ:
        os.environ["QT_IM_MODULE"] = "xim"
    app = QApplication(sys.argv)
    w = TiffPlayerQt()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
