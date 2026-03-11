#!/usr/bin/env python3
"""
Morphometric Classification GUI
PyQt6 desktop application for running advanced morphometric classification
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PyQt6.QtCore import QProcess, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ScriptRunnerThread(QThread):
    """Background thread for running the morphometric script"""

    output_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, script_path: str, script_args: List[str]):
        super().__init__()
        self.script_path = script_path
        self.script_args = script_args
        self.process = None

    def run(self):
        """Execute the morphometric classification script"""
        try:
            cmd = [sys.executable, self.script_path] + self.script_args
            self.output_signal.emit(f"Starting: {' '.join(cmd)}\n")

            self.process = QProcess()
            self.process.setProcessChannelMode(
                QProcess.ProcessChannelMode.MergedChannels
            )

            # Connect to read ready signal
            self.process.readyReadStandardOutput.connect(self._on_ready_read)

            self.process.start(sys.executable, [self.script_path] + self.script_args)

            # Wait for process to finish
            if self.process.waitForFinished(-1):
                if self.process.exitCode() == 0:
                    self.output_signal.emit("\n✓ Script completed successfully!\n")
                    self.finished_signal.emit(True, "Script completed successfully!")
                else:
                    error_msg = f"Script exited with code {self.process.exitCode()}"
                    self.output_signal.emit(f"\n✗ {error_msg}\n")
                    self.finished_signal.emit(False, error_msg)
            else:
                error_msg = "Script execution failed"
                self.output_signal.emit(f"\n✗ {error_msg}\n")
                self.finished_signal.emit(False, error_msg)

        except Exception as e:
            error_msg = str(e)
            self.output_signal.emit(f"\n✗ Error: {error_msg}\n")
            self.finished_signal.emit(False, error_msg)

    def _on_ready_read(self):
        """Read available output from process"""
        if self.process:
            output = (
                self.process.readAllStandardOutput()
                .data()
                .decode("utf-8", errors="replace")
            )
            self.output_signal.emit(output)

    def stop(self):
        """Stop the running process"""
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.process.waitForFinished(3000)


class MorphometricsGUI(QMainWindow):
    """Main GUI window for morphometric classification"""

    def __init__(self):
        super().__init__()
        self.script_path = self._find_script()
        self.runner_thread = None
        self.init_ui()
        self.load_settings()

    def _find_script(self) -> str:
        """Find the morphometric classification script"""
        script_name = "02_Advanced_Morphometric_Classification.py"

        # Try current directory
        if os.path.exists(script_name):
            return os.path.abspath(script_name)

        # Try Materials directory
        materials_dir = Path(__file__).parent / "Materials"
        script_path = materials_dir / script_name
        if script_path.exists():
            return str(script_path)

        # Try parent directory
        parent_script = Path(__file__).parent.parent / script_name
        if parent_script.exists():
            return str(parent_script)

        # Try finding it in the project
        possible_paths = [
            os.path.expanduser(
                "~/Desktop/Lund_Master/Courses/BINP29/Morphometrics/Materials"
            )
            / script_name,
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return str(path)

        return script_name

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Morphometric Classification GUI")
        self.setGeometry(100, 100, 1000, 800)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Add tabs
        self.tabs.addTab(self._create_datasets_tab(), "Datasets")
        self.tabs.addTab(self._create_settings_tab(), "Settings")
        self.tabs.addTab(self._create_console_tab(), "Console Output")
        self.tabs.addTab(self._create_results_tab(), "Results")

        # Control buttons
        button_layout = QHBoxLayout()

        self.run_button = QPushButton("Run Analysis")
        self.run_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.run_button.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 8px;"
        )
        self.run_button.clicked.connect(self.run_analysis)
        button_layout.addWidget(self.run_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(
            "background-color: #f44336; color: white; padding: 8px;"
        )
        self.stop_button.clicked.connect(self.stop_analysis)
        button_layout.addWidget(self.stop_button)

        self.open_results_button = QPushButton("Open Results Folder")
        self.open_results_button.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 8px;"
        )
        self.open_results_button.clicked.connect(self.open_results_folder)
        button_layout.addWidget(self.open_results_button)

        main_layout.addLayout(button_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(self.status_label)

        main_widget.setLayout(main_layout)

    def _create_datasets_tab(self) -> QWidget:
        """Create the datasets selection tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select Datasets to Process:"))
        layout.addWidget(QLabel("(Uncheck to skip a dataset)"))
        layout.addSpacing(10)

        # Dataset definitions
        self.datasets = {
            "Canids": ("Canids/raw_data/canids_morphologika.txt", "canids", True),
            "Hominids": (
                "Hominids/raw_data/landmarks_paper_morphologika.txt",
                "hominids",
                True,
            ),
            "Papionins": (
                "Papionins/raw_data/cercocebus,macaca mandrilus, papio and lophocebus adults .txt",
                "papionins",
                True,
            ),
            "Bears": ("Bears/raw_data/bears_morphologika.txt", "bears", True),
            "Quolls": ("Quolls/raw_data/quolls_morphologika.txt", "quolls", True),
            "Wolves": ("Wolf/raw_data/wolf_morphologika.txt", "wolves", True),
            "Aariz": ("Aariz/raw_data/aariz_morphologika.txt", "aariz", True),
        }

        self.dataset_checkboxes = {}
        for name, (path, dtype, default) in self.datasets.items():
            checkbox = QCheckBox(f"{name} ({dtype})")
            checkbox.setChecked(default)
            self.dataset_checkboxes[name] = checkbox
            layout.addWidget(checkbox)

        layout.addSpacing(20)
        layout.addWidget(QLabel("Dataset Information:"))

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setText("""
Canids: 3D, 117 specimens, 41 landmarks, 3 classes
Hominids: 3D, 75 specimens, 10 landmarks, 3 classes
Papionins: 3D, 93 specimens, 31 landmarks, 5 classes
Bears: 3D, 48 specimens, 39 landmarks, 3 classes
Quolls: 3D, 101 specimens, 101 landmarks, 5 classes
Wolves: 3D, 84 specimens, 54 landmarks, 6 classes
Aariz: 2D, 1000 specimens, 29 landmarks, 6 classes

Note: Scripts filters out rare species (< 3 samples)
        """)
        layout.addWidget(info_text)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_settings_tab(self) -> QWidget:
        """Create the settings configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Scrollable area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Random State
        group = QGroupBox("Random State & Cross-Validation")
        group_layout = QVBoxLayout()

        self.random_state_spinbox = QSpinBox()
        self.random_state_spinbox.setValue(42)
        self.random_state_spinbox.setRange(0, 10000)
        group_layout.addWidget(QLabel("Random State (for reproducibility):"))
        group_layout.addWidget(self.random_state_spinbox)

        self.n_splits_spinbox = QSpinBox()
        self.n_splits_spinbox.setValue(5)
        self.n_splits_spinbox.setRange(2, 20)
        group_layout.addWidget(QLabel("Number of CV Folds:"))
        group_layout.addWidget(self.n_splits_spinbox)

        self.min_samples_spinbox = QSpinBox()
        self.min_samples_spinbox.setValue(3)
        self.min_samples_spinbox.setRange(1, 50)
        group_layout.addWidget(QLabel("Minimum Samples per Class:"))
        group_layout.addWidget(self.min_samples_spinbox)

        group.setLayout(group_layout)
        scroll_layout.addWidget(group)

        # Ensemble Tuning
        group = QGroupBox("Ensemble Tuning")
        group_layout = QVBoxLayout()

        self.tune_voting_checkbox = QCheckBox("Tune Weighted Voting Ensemble")
        self.tune_voting_checkbox.setChecked(True)
        group_layout.addWidget(self.tune_voting_checkbox)

        self.global_tune_checkbox = QCheckBox(
            "Global Tune Weighted Voting (across all datasets)"
        )
        self.global_tune_checkbox.setChecked(True)
        group_layout.addWidget(self.global_tune_checkbox)

        group.setLayout(group_layout)
        scroll_layout.addWidget(group)

        # Feature Engineering
        group = QGroupBox("Feature Engineering")
        group_layout = QVBoxLayout()

        features_text = QTextEdit()
        features_text.setReadOnly(True)
        features_text.setText("""
The script computes comprehensive shape features (NO PCA):

✓ All pairwise distances between landmarks
✓ Interlandmark angles (triplet combinations)
✓ Centroid-based features
✓ Bounding box dimensions & aspect ratios
✓ Statistical moments (skewness, kurtosis)
✓ Eigenvalues (shape descriptors)
✓ Scale-invariant distance ratios
        """)
        group_layout.addWidget(features_text)
        group.setLayout(group_layout)
        scroll_layout.addWidget(group)

        # Models
        group = QGroupBox("Machine Learning Models")
        group_layout = QVBoxLayout()

        models_text = QTextEdit()
        models_text.setReadOnly(True)
        models_text.setText("""
11 Base Models:
• XGBoost, LightGBM, CatBoost (Gradient Boosting)
• Random Forest, Extra Trees, Gradient Boosting
• Logistic Regression, Linear Discriminant Analysis
• Support Vector Machine, Multi-layer Perceptron
• K-Nearest Neighbors

3 Ensemble Methods:
• Stacking (with meta-learner)
• Blending (holdout validation)
• Weighted Voting (tuned by accuracy)

All evaluated with stratified K-fold cross-validation
        """)
        group_layout.addWidget(models_text)
        group.setLayout(group_layout)
        scroll_layout.addWidget(group)

        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)

        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget

    def _create_console_tab(self) -> QWidget:
        """Create the console output tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Script Output:"))

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Courier", 9))
        layout.addWidget(self.console_output)

        widget.setLayout(layout)
        return widget

    def _create_results_tab(self) -> QWidget:
        """Create the results viewing tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Analysis Results:"))

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Arial", 10))
        layout.addWidget(self.results_text)

        results_info = QTextEdit()
        results_info.setReadOnly(True)
        results_info.setMaximumHeight(150)
        results_info.setText("""
Output Files Generated:
• Advanced_Classification_Results.xlsx - All results in Excel format
• [Dataset]_Confusion_Matrix_Best_Overall.png - Visualization per dataset
• run.log.txt - Full console output log
• weighted_voting_tuned_params.json - Tuned ensemble parameters

Location: 02_Advanced_Morphometric_Classification_outputs/
        """)
        layout.addWidget(results_info)

        widget.setLayout(layout)
        return widget

    def run_analysis(self):
        """Run the morphometric classification script"""
        # Check if script exists
        if not os.path.exists(self.script_path):
            QMessageBox.warning(
                self,
                "Script Not Found",
                f"Could not find script at:\n{self.script_path}\n\n"
                "Please ensure the script is in the same directory as this GUI.",
            )
            return

        # Get selected datasets
        selected_datasets = [
            name
            for name, checkbox in self.dataset_checkboxes.items()
            if checkbox.isChecked()
        ]

        if not selected_datasets:
            QMessageBox.warning(
                self,
                "No Datasets Selected",
                "Please select at least one dataset to process.",
            )
            return

        # Disable run button, enable stop button
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Running analysis...")
        self.status_label.setStyleSheet(
            "color: #FF9800; font-style: italic; font-weight: bold;"
        )

        # Clear console
        self.console_output.clear()
        self.results_text.clear()

        # Log settings
        log_message = f"""
{"=" * 70}
MORPHOMETRIC CLASSIFICATION - GUI RUN
{"=" * 70}
Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

CONFIGURATION:
  Random State: {self.random_state_spinbox.value()}
  CV Folds: {self.n_splits_spinbox.value()}
  Min Samples per Class: {self.min_samples_spinbox.value()}
  Tune Weighted Voting: {self.tune_voting_checkbox.isChecked()}
  Global Tune: {self.global_tune_checkbox.isChecked()}

SELECTED DATASETS:
  {", ".join(selected_datasets)}

SCRIPT: {self.script_path}
{"=" * 70}

"""
        self.console_output.setText(log_message)

        # Build arguments (would need to modify the script to accept CLI args)
        # For now, we'll just run the script as-is
        script_args = []

        # Start runner thread
        self.runner_thread = ScriptRunnerThread(self.script_path, script_args)
        self.runner_thread.output_signal.connect(self._append_console_output)
        self.runner_thread.finished_signal.connect(self._on_script_finished)
        self.runner_thread.start()

    def stop_analysis(self):
        """Stop the running analysis"""
        if self.runner_thread:
            self.runner_thread.stop()
            self.console_output.appendPlainText("\n[USER] Analysis stopped by user.")
            self._on_script_finished(False, "Stopped by user")

    def _append_console_output(self, text: str):
        """Append text to console output"""
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console_output.setTextCursor(cursor)
        self.console_output.insertPlainText(text)
        self.console_output.ensureCursorVisible()

    def _on_script_finished(self, success: bool, message: str):
        """Handle script completion"""
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if success:
            self.status_label.setText(f"✓ {message}")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self._load_and_display_results()
            QMessageBox.information(
                self,
                "Analysis Complete",
                f"✓ {message}\n\nResults have been saved to the output directory.",
            )
        else:
            self.status_label.setText(f"✗ {message}")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
            QMessageBox.warning(
                self,
                "Analysis Failed",
                f"✗ {message}\n\nCheck the console output for details.",
            )

    def _load_and_display_results(self):
        """Load and display results from output directory"""
        try:
            # Find output directory
            script_dir = os.path.dirname(self.script_path)
            output_dir = os.path.join(
                script_dir, "02_Advanced_Morphometric_Classification_outputs"
            )

            if not os.path.exists(output_dir):
                output_dir = os.path.join(
                    os.path.dirname(script_dir),
                    "02_Advanced_Morphometric_Classification_outputs",
                )

            results_info = f"""
Analysis Results Summary
{"=" * 50}

Output Directory: {output_dir}

Generated Files:
"""

            if os.path.exists(output_dir):
                for file in sorted(os.listdir(output_dir)):
                    file_path = os.path.join(output_dir, file)
                    size = os.path.getsize(file_path) / 1024  # KB
                    results_info += f"  ✓ {file} ({size:.1f} KB)\n"

            results_info += f"""

{"=" * 50}
Analysis completed successfully!
Open the Excel file to view detailed results.
            """

            self.results_text.setText(results_info)

        except Exception as e:
            self.results_text.setText(f"Could not load results: {str(e)}")

    def open_results_folder(self):
        """Open the results folder in file explorer"""
        script_dir = os.path.dirname(self.script_path)
        output_dir = os.path.join(
            script_dir, "02_Advanced_Morphometric_Classification_outputs"
        )

        if not os.path.exists(output_dir):
            output_dir = os.path.join(
                os.path.dirname(script_dir),
                "02_Advanced_Morphometric_Classification_outputs",
            )

        if os.path.exists(output_dir):
            if sys.platform == "darwin":  # macOS
                subprocess.Popen(["open", output_dir])
            elif sys.platform == "win32":  # Windows
                subprocess.Popen(["explorer", output_dir])
            else:  # Linux
                subprocess.Popen(["xdg-open", output_dir])
        else:
            QMessageBox.warning(
                self,
                "Directory Not Found",
                f"Output directory not found:\n{output_dir}\n\nRun the analysis first to generate results.",
            )

    def load_settings(self):
        """Load settings from config file if it exists"""
        config_file = "morphometrics_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    self.random_state_spinbox.setValue(config.get("random_state", 42))
                    self.n_splits_spinbox.setValue(config.get("n_splits", 5))
                    self.min_samples_spinbox.setValue(config.get("min_samples", 3))
                    self.tune_voting_checkbox.setChecked(
                        config.get("tune_voting", True)
                    )
                    self.global_tune_checkbox.setChecked(
                        config.get("global_tune", True)
                    )
            except:
                pass

    def save_settings(self):
        """Save settings to config file"""
        config = {
            "random_state": self.random_state_spinbox.value(),
            "n_splits": self.n_splits_spinbox.value(),
            "min_samples": self.min_samples_spinbox.value(),
            "tune_voting": self.tune_voting_checkbox.isChecked(),
            "global_tune": self.global_tune_checkbox.isChecked(),
        }
        try:
            with open("morphometrics_config.json", "w") as f:
                json.dump(config, f, indent=2)
        except:
            pass

    def closeEvent(self, event):
        """Handle window close event"""
        if self.runner_thread and self.runner_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Analysis Running",
                "Analysis is still running. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.runner_thread.stop()
                self.runner_thread.wait()
                self.save_settings()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_settings()
            event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    window = MorphometricsGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
