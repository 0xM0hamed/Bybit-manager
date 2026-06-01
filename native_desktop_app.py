#!/usr/bin/env python3
"""
Bybit Account Manager - Native Desktop Application
Pure PyQt6 application - no web server needed
"""

import sys
import os
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog, QLabel,
    QLineEdit, QComboBox, QMessageBox, QHeaderView, QButtonGroup,
    QRadioButton, QFrame, QFileDialog, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QIcon

# When frozen by PyInstaller, bundled assets live in sys._MEIPASS (temp extraction folder).
# User data (accounts_data.json) must live next to the .exe so it persists between runs.
if getattr(sys, 'frozen', False):
    _EXE_DIR    = os.path.dirname(sys.executable)   # folder containing the .exe
    _ASSETS_DIR = sys._MEIPASS                       # bundled read-only assets
else:
    _EXE_DIR    = os.path.dirname(os.path.abspath(__file__))
    _ASSETS_DIR = _EXE_DIR

DATA_FILE = os.path.join(_EXE_DIR, 'accounts_data.json')

class AccountManager:
    """Handles all account data operations"""
    
    @staticmethod
    def load_accounts():
        """Load accounts from JSON file"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        return []
    
    @staticmethod
    def save_accounts(accounts):
        """Save accounts to JSON file"""
        with open(DATA_FILE, 'w') as f:
            json.dump(accounts, f, indent=2)
    
    @staticmethod
    def calculate_profit_loss(account):
        """Calculate profit/loss for an account"""
        total_costs = (
            float(account.get('kyc_cost', 0)) +
            float(account.get('selfie_cost', 0)) +
            float(account.get('additional_costs', 0))
        )
        deposits = float(account.get('deposits', 0))
        withdrawn = float(account.get('withdrawn', 0))
        status = account.get('status', '')
        
        # For "in_progress" accounts, add deposits to P/L since money is still in account
        if status == 'in_progress':
            profit_loss = (withdrawn + deposits) - (deposits + total_costs)
        else:
            profit_loss = withdrawn - (deposits + total_costs)
        
        return profit_loss
    
    @staticmethod
    def get_next_id(accounts):
        """Get next available ID"""
        if not accounts:
            return 1
        return max(acc['id'] for acc in accounts) + 1


class AccountDialog(QDialog):
    """Dialog for adding/editing accounts"""
    
    def __init__(self, parent=None, account=None):
        super().__init__(parent)
        self.account = account
        self.setup_ui()
        
        if account:
            self.load_account_data()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle('Add New Account' if not self.account else 'Edit Account')
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #333333;
                font-weight: bold;
                margin-top: 8px;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: white;
                color: #333333;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #667eea;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Gmail
        layout.addWidget(QLabel('Gmail Address *'))
        self.gmail_input = QLineEdit()
        layout.addWidget(self.gmail_input)
        
        # Leader
        layout.addWidget(QLabel('Leader (Phone/Username) *'))
        self.leader_input = QLineEdit()
        layout.addWidget(self.leader_input)
        
        # Verifier Name
        layout.addWidget(QLabel('Verifier Full Name *'))
        self.verifier_input = QLineEdit()
        layout.addWidget(self.verifier_input)
        
        # Status
        layout.addWidget(QLabel('Status *'))
        self.status_combo = QComboBox()
        self.status_combo.addItems(['In Progress', 'Done & Eligible', 'Done (Not Eligible)'])
        layout.addWidget(self.status_combo)
        
        # KYC Cost
        layout.addWidget(QLabel('KYC Cost ($)'))
        self.kyc_input = QLineEdit('0')
        layout.addWidget(self.kyc_input)
        
        # Selfie Cost
        layout.addWidget(QLabel('Selfie Cost ($)'))
        self.selfie_input = QLineEdit('0')
        layout.addWidget(self.selfie_input)
        
        # Additional Costs
        layout.addWidget(QLabel('Additional Costs ($)'))
        self.additional_input = QLineEdit('0')
        layout.addWidget(self.additional_input)
        
        # Deposits
        layout.addWidget(QLabel('Deposits ($)'))
        self.deposits_input = QLineEdit('0')
        layout.addWidget(self.deposits_input)
        
        # Withdrawn
        layout.addWidget(QLabel('Total Withdrawn ($)'))
        self.withdrawn_input = QLineEdit('0')
        layout.addWidget(self.withdrawn_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 20, 0, 0)
        
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet('background-color: #6b7280; color: white;')
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton('Save Account')
        save_btn.clicked.connect(self.save_account)
        save_btn.setStyleSheet('background-color: #667eea; color: white;')
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_account_data(self):
        """Load existing account data into form"""
        self.gmail_input.setText(self.account.get('gmail', ''))
        self.leader_input.setText(self.account.get('leader', ''))
        self.verifier_input.setText(self.account.get('verifier_name', ''))
        self.kyc_input.setText(str(self.account.get('kyc_cost', 0)))
        self.selfie_input.setText(str(self.account.get('selfie_cost', 0)))
        self.additional_input.setText(str(self.account.get('additional_costs', 0)))
        self.deposits_input.setText(str(self.account.get('deposits', 0)))
        self.withdrawn_input.setText(str(self.account.get('withdrawn', 0)))
        
        status = self.account.get('status', 'in_progress')
        if status == 'in_progress':
            self.status_combo.setCurrentIndex(0)
        elif status == 'done_eligible':
            self.status_combo.setCurrentIndex(1)
        else:
            self.status_combo.setCurrentIndex(2)
    
    def save_account(self):
        """Validate and save account data"""
        # Validation
        if not self.gmail_input.text():
            QMessageBox.warning(self, 'Error', 'Gmail address is required')
            return
        
        if not self.leader_input.text():
            QMessageBox.warning(self, 'Error', 'Leader is required')
            return
        
        if not self.verifier_input.text():
            QMessageBox.warning(self, 'Error', 'Verifier name is required')
            return
        
        # Get status value
        status_map = {
            0: 'in_progress',
            1: 'done_eligible',
            2: 'done_not_eligible'
        }
        
        # Create account data
        self.account_data = {
            'gmail': self.gmail_input.text(),
            'leader': self.leader_input.text(),
            'verifier_name': self.verifier_input.text(),
            'kyc_cost': float(self.kyc_input.text() or 0),
            'selfie_cost': float(self.selfie_input.text() or 0),
            'additional_costs': float(self.additional_input.text() or 0),
            'deposits': float(self.deposits_input.text() or 0),
            'withdrawn': float(self.withdrawn_input.text() or 0),
            'status': status_map[self.status_combo.currentIndex()]
        }
        
        self.accept()


class SettingsDialog(QDialog):
    """Settings dialog with backup and import actions"""

    DIALOG_STYLE = """
        QDialog {
            background-color: #f8f9fa;
        }
        QLabel#section_title {
            color: #667eea;
            font-size: 13px;
            font-weight: bold;
            padding-top: 6px;
        }
        QLabel#desc {
            color: #6b7280;
            font-size: 12px;
        }
        QPushButton.action_btn {
            padding: 10px 18px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 13px;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet(self.DIALOG_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # ── Title ──────────────────────────────────────────────
        title = QLabel('⚙️  Settings')
        f = QFont()
        f.setPointSize(15)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet('color: #333333;')
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('color: #e5e7eb;')
        layout.addWidget(sep)

        # ── Backup section ─────────────────────────────────────
        backup_title = QLabel('💾  Backup Data')
        backup_title.setObjectName('section_title')
        layout.addWidget(backup_title)

        backup_desc = QLabel('Save a copy of all your accounts to a JSON file.')
        backup_desc.setObjectName('desc')
        backup_desc.setWordWrap(True)
        layout.addWidget(backup_desc)

        backup_btn = QPushButton('Export Backup…')
        backup_btn.setStyleSheet(
            'background-color: #667eea; color: white; padding: 10px 18px;'
            'border-radius: 6px; font-weight: bold; font-size: 13px;'
        )
        backup_btn.clicked.connect(self._backup)
        layout.addWidget(backup_btn)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet('color: #e5e7eb;')
        layout.addWidget(sep2)

        # ── Import section ─────────────────────────────────────
        import_title = QLabel('📂  Import Data')
        import_title.setObjectName('section_title')
        layout.addWidget(import_title)

        import_desc = QLabel(
            'Load accounts from a backup file.\n'
            '• Replace — clears current data and loads the backup.\n'
            '• Merge — adds backup accounts that don\'t already exist (matched by Gmail).'
        )
        import_desc.setObjectName('desc')
        import_desc.setWordWrap(True)
        layout.addWidget(import_desc)

        import_row = QHBoxLayout()
        import_row.setSpacing(8)

        replace_btn = QPushButton('Replace Import…')
        replace_btn.setStyleSheet(
            'background-color: #ef4444; color: white; padding: 10px 18px;'
            'border-radius: 6px; font-weight: bold; font-size: 13px;'
        )
        replace_btn.clicked.connect(lambda: self._import(merge=False))
        import_row.addWidget(replace_btn)

        merge_btn = QPushButton('Merge Import…')
        merge_btn.setStyleSheet(
            'background-color: #10b981; color: white; padding: 10px 18px;'
            'border-radius: 6px; font-weight: bold; font-size: 13px;'
        )
        merge_btn.clicked.connect(lambda: self._import(merge=True))
        import_row.addWidget(merge_btn)

        layout.addLayout(import_row)

        # ── Close ──────────────────────────────────────────────
        layout.addStretch()
        close_btn = QPushButton('Close')
        close_btn.setStyleSheet(
            'background-color: #6b7280; color: white; padding: 10px 18px;'
            'border-radius: 6px; font-weight: bold; font-size: 13px;'
        )
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    # ── Actions ────────────────────────────────────────────────

    def _backup(self):
        """Export current data to a user-chosen JSON file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f'bybit_backup_{timestamp}.json'

        path, _ = QFileDialog.getSaveFileName(
            self, 'Save Backup', default_name,
            'JSON Files (*.json);;All Files (*)'
        )
        if not path:
            return

        try:
            shutil.copy2(DATA_FILE, path)
            QMessageBox.information(
                self, 'Backup Saved',
                f'Backup saved successfully to:\n{path}'
            )
        except Exception as e:
            QMessageBox.critical(self, 'Backup Failed', f'Could not save backup:\n{e}')

    def _import(self, merge: bool):
        """Import accounts from a backup JSON file."""
        path, _ = QFileDialog.getOpenFileName(
            self, 'Open Backup File', '',
            'JSON Files (*.json);;All Files (*)'
        )
        if not path:
            return

        try:
            with open(path, 'r') as f:
                imported = json.load(f)

            if not isinstance(imported, list):
                QMessageBox.warning(self, 'Invalid File',
                                    'The selected file does not contain a valid accounts list.')
                return

            current = AccountManager.load_accounts()

            if merge:
                existing_gmails = {acc.get('gmail', '').lower() for acc in current}
                new_accounts = [a for a in imported
                                if a.get('gmail', '').lower() not in existing_gmails]
                # Re-assign IDs to avoid collisions
                next_id = AccountManager.get_next_id(current) if current else 1
                for acc in new_accounts:
                    acc['id'] = next_id
                    next_id += 1
                merged = current + new_accounts
                AccountManager.save_accounts(merged)
                QMessageBox.information(
                    self, 'Import Complete',
                    f'Merged {len(new_accounts)} new account(s) into your data.'
                )
            else:
                confirm = QMessageBox.question(
                    self, 'Confirm Replace',
                    f'This will DELETE all {len(current)} current account(s) and replace them '
                    f'with {len(imported)} account(s) from the backup.\n\nContinue?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    return
                AccountManager.save_accounts(imported)
                QMessageBox.information(
                    self, 'Import Complete',
                    f'Replaced data with {len(imported)} account(s) from backup.'
                )

            # Signal the main window to reload
            self.data_changed = True

        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Import Failed', 'The file is not valid JSON.')
        except Exception as e:
            QMessageBox.critical(self, 'Import Failed', f'Could not import data:\n{e}')


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_filter = 'all'
        self.setup_ui()
        self.load_data()

    def open_settings(self):
        """Open the settings dialog and reload data if it changed."""
        dialog = SettingsDialog(self)
        dialog.data_changed = False
        dialog.exec()
        if dialog.data_changed:
            self.load_data()
    
    def setup_ui(self):
        """Setup the main window UI"""
        self.setWindowTitle('Bybit Account Manager')
        self.setGeometry(100, 100, 1400, 800)
        
        # Set window icon — look in the assets dir (sys._MEIPASS when frozen)
        icon_path = os.path.join(_ASSETS_DIR, 'Bybit.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel('📊 Bybit Account Manager')
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet('color: #333333;')
        header_layout.addWidget(title)
        
        header_layout.addStretch()

        settings_btn = QPushButton('⚙️')
        settings_btn.setToolTip('Settings — Backup & Import')
        settings_btn.setFixedSize(42, 42)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #667eea;
                border: 2px solid #667eea;
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #667eea;
                color: white;
            }
        """)
        settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(settings_btn)

        new_btn = QPushButton('+ New Account')
        new_btn.setStyleSheet('background-color: #667eea; color: white; padding: 10px 20px; font-weight: bold; border-radius: 6px;')
        new_btn.clicked.connect(self.add_account)
        header_layout.addWidget(new_btn)
        
        main_layout.addLayout(header_layout)
        
        # Summary card
        summary_frame = QFrame()
        summary_frame.setStyleSheet('background-color: white; border-radius: 8px; padding: 15px;')
        summary_layout = QVBoxLayout()
        
        summary_title = QLabel('Total Summary')
        summary_title_font = QFont()
        summary_title_font.setPointSize(14)
        summary_title_font.setBold(True)
        summary_title.setFont(summary_title_font)
        summary_title.setStyleSheet('color: #333333;')
        summary_layout.addWidget(summary_title)
        
        stats_layout = QHBoxLayout()
        
        self.total_accounts_label = QLabel('Total Accounts: 0')
        self.total_accounts_label.setStyleSheet('color: #333333; font-size: 14px;')
        stats_layout.addWidget(self.total_accounts_label)
        
        self.total_pl_label = QLabel('Total P/L: $0.00')
        self.total_pl_label.setStyleSheet('color: #333333; font-size: 14px;')
        stats_layout.addWidget(self.total_pl_label)
        
        self.total_in_accounts_label = QLabel('Total In-Accounts: $0.00')
        self.total_in_accounts_label.setStyleSheet('color: #3b82f6; font-size: 14px; font-weight: bold;')
        stats_layout.addWidget(self.total_in_accounts_label)
        
        stats_layout.addStretch()
        
        summary_layout.addLayout(stats_layout)
        summary_frame.setLayout(summary_layout)
        main_layout.addWidget(summary_frame)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        
        self.filter_all_btn = QPushButton('All')
        self.filter_all_btn.setCheckable(True)
        self.filter_all_btn.setChecked(True)
        self.filter_all_btn.clicked.connect(lambda: self.filter_accounts('all'))
        self.filter_all_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333333;
                border: 2px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #667eea;
                color: white;
                border-color: #667eea;
            }
        """)
        filter_layout.addWidget(self.filter_all_btn)
        
        self.filter_progress_btn = QPushButton('In Progress')
        self.filter_progress_btn.setCheckable(True)
        self.filter_progress_btn.clicked.connect(lambda: self.filter_accounts('in_progress'))
        self.filter_progress_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333333;
                border: 2px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #667eea;
                color: white;
                border-color: #667eea;
            }
        """)
        filter_layout.addWidget(self.filter_progress_btn)
        
        self.filter_eligible_btn = QPushButton('Done & Eligible')
        self.filter_eligible_btn.setCheckable(True)
        self.filter_eligible_btn.clicked.connect(lambda: self.filter_accounts('done_eligible'))
        self.filter_eligible_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333333;
                border: 2px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #667eea;
                color: white;
                border-color: #667eea;
            }
        """)
        filter_layout.addWidget(self.filter_eligible_btn)
        
        self.filter_not_eligible_btn = QPushButton('Done (Not Eligible)')
        self.filter_not_eligible_btn.setCheckable(True)
        self.filter_not_eligible_btn.clicked.connect(lambda: self.filter_accounts('done_not_eligible'))
        self.filter_not_eligible_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333333;
                border: 2px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #667eea;
                color: white;
                border-color: #667eea;
            }
        """)
        filter_layout.addWidget(self.filter_not_eligible_btn)
        
        filter_layout.addStretch()
        
        main_layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Gmail', 'Leader', 'Verifier', 'KYC Cost', 
            'Selfie Cost', 'Additional', 'Deposits', 'Withdrawn', 
            'P/L', 'Status', 'Actions'
        ])
        
        # Set fixed row height (taller to fit buttons)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.verticalHeader().setVisible(False)
        
        header = self.table.horizontalHeader()
        
        # Set custom column widths for optimal layout
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        self.table.setColumnWidth(0, 50)
        
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Gmail
        self.table.setColumnWidth(1, 250)
        
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Leader
        self.table.setColumnWidth(2, 120)
        
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Verifier
        self.table.setColumnWidth(3, 200)
        
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # KYC Cost
        self.table.setColumnWidth(4, 100)
        
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Selfie Cost
        self.table.setColumnWidth(5, 100)
        
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Additional
        self.table.setColumnWidth(6, 100)
        
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # Deposits
        self.table.setColumnWidth(7, 100)
        
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)  # Withdrawn
        self.table.setColumnWidth(8, 100)
        
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)  # P/L
        self.table.setColumnWidth(9, 100)
        
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Stretch)  # Status - stretch to fill
        
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.Fixed)  # Actions
        self.table.setColumnWidth(11, 200)
        
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9fafb;
                color: #333333;
                gridline-color: #e5e7eb;
                border: none;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #333333;
                padding: 12px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid #e5e7eb;
            }
            QTableWidget::item {
                padding: 12px;
                color: #333333;
            }
        """)
        
        main_layout.addWidget(self.table)
        
        central_widget.setLayout(main_layout)
        
        # Set main window style
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            QWidget {
                color: #333333;
            }
        """)
    
    def load_data(self):
        """Load and display account data"""
        self.accounts = AccountManager.load_accounts()
        self.update_summary()
        self.update_table()
    
    def update_summary(self):
        """Update summary statistics"""
        total_accounts = len(self.accounts)
        
        # Calculate totals
        total_pl = sum(AccountManager.calculate_profit_loss(acc) for acc in self.accounts)
        total_in_accounts = sum(
            float(acc.get('deposits', 0))
            for acc in self.accounts
            if acc.get('status') == 'in_progress'
        )
        
        self.total_accounts_label.setText(f'Total Accounts: {total_accounts}')
        self.total_accounts_label.setStyleSheet('color: #333333; font-size: 14px; font-weight: bold;')
        
        pl_color = '#10b981' if total_pl >= 0 else '#ef4444'
        self.total_pl_label.setText(f'Total P/L: ${total_pl:.2f}')
        self.total_pl_label.setStyleSheet(f'color: {pl_color}; font-size: 14px; font-weight: bold;')
        
        self.total_in_accounts_label.setText(f'Total In-Accounts: ${total_in_accounts:.2f}')
        self.total_in_accounts_label.setStyleSheet('color: #3b82f6; font-size: 14px; font-weight: bold;')
    
    def update_table(self):
        """Update the accounts table"""
        # Filter accounts
        if self.current_filter == 'all':
            filtered_accounts = self.accounts
        else:
            filtered_accounts = [acc for acc in self.accounts if acc.get('status') == self.current_filter]
        
        self.table.setRowCount(len(filtered_accounts))
        
        for row, account in enumerate(filtered_accounts):
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(account['id'])))
            
            # Gmail
            self.table.setItem(row, 1, QTableWidgetItem(account.get('gmail', '')))
            
            # Leader
            self.table.setItem(row, 2, QTableWidgetItem(account.get('leader', '')))
            
            # Verifier
            self.table.setItem(row, 3, QTableWidgetItem(account.get('verifier_name', '')))
            
            # Costs and amounts
            self.table.setItem(row, 4, QTableWidgetItem(f"${account.get('kyc_cost', 0):.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"${account.get('selfie_cost', 0):.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"${account.get('additional_costs', 0):.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(f"${account.get('deposits', 0):.2f}"))
            self.table.setItem(row, 8, QTableWidgetItem(f"${account.get('withdrawn', 0):.2f}"))
            
            # P/L
            pl = AccountManager.calculate_profit_loss(account)
            pl_item = QTableWidgetItem(f"${pl:.2f}")
            pl_item.setFont(QFont('', -1, QFont.Weight.Bold))
            
            # Color code P/L with background colors
            if pl >= 0:
                pl_item.setForeground(QColor('#16a34a'))  # Bright Green
                pl_item.setBackground(QColor('#dcfce7'))  # Light Green background
            else:
                pl_item.setForeground(QColor('#dc2626'))  # Bright Red
                pl_item.setBackground(QColor('#fee2e2'))  # Light Red background
            
            self.table.setItem(row, 9, pl_item)
            
            # Status
            status = account.get('status', 'in_progress')
            status_text = {
                'in_progress': 'In Progress',
                'done_eligible': 'Done & Eligible',
                'done_not_eligible': 'Done (Not Eligible)'
            }.get(status, status)
            
            status_item = QTableWidgetItem(status_text)
            status_item.setFont(QFont('', -1, QFont.Weight.Bold))
            
            # Color code status with background colors matching P/L style
            if status == 'in_progress':
                status_item.setForeground(QColor('#2563eb'))  # Bright Blue
                status_item.setBackground(QColor('#dbeafe'))  # Light Blue background
            elif status == 'done_eligible':
                status_item.setForeground(QColor('#16a34a'))  # Bright Green (same as profit)
                status_item.setBackground(QColor('#dcfce7'))  # Light Green background (same as profit)
            else:  # done_not_eligible
                status_item.setForeground(QColor('#dc2626'))  # Bright Red (same as loss)
                status_item.setBackground(QColor('#fee2e2'))  # Light Red background (same as loss)
            
            self.table.setItem(row, 10, status_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(5, 5, 5, 5)
            actions_layout.setSpacing(5)
            
            edit_btn = QPushButton('✏️ Edit')
            edit_btn.setMinimumHeight(40)
            edit_btn.setMinimumWidth(80)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            edit_btn.clicked.connect(lambda checked, acc=account: self.edit_account(acc))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton('🗑️ Delete')
            delete_btn.setMinimumHeight(40)
            delete_btn.setMinimumWidth(80)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
            """)
            delete_btn.clicked.connect(lambda checked, acc=account: self.delete_account(acc))
            actions_layout.addWidget(delete_btn)
            
            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 11, actions_widget)
    
    def filter_accounts(self, filter_type):
        """Filter accounts by status"""
        self.current_filter = filter_type
        
        # Update button states
        self.filter_all_btn.setChecked(filter_type == 'all')
        self.filter_progress_btn.setChecked(filter_type == 'in_progress')
        self.filter_eligible_btn.setChecked(filter_type == 'done_eligible')
        self.filter_not_eligible_btn.setChecked(filter_type == 'done_not_eligible')
        
        self.update_table()
    
    def add_account(self):
        """Open dialog to add new account"""
        dialog = AccountDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            account_data = dialog.account_data
            account_data['id'] = AccountManager.get_next_id(self.accounts)
            account_data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.accounts.append(account_data)
            AccountManager.save_accounts(self.accounts)
            self.load_data()
    
    def edit_account(self, account):
        """Open dialog to edit account"""
        dialog = AccountDialog(self, account)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update account
            for key, value in dialog.account_data.items():
                account[key] = value
            account['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            AccountManager.save_accounts(self.accounts)
            self.load_data()
    
    def delete_account(self, account):
        """Delete an account"""
        reply = QMessageBox.question(
            self,
            'Confirm Delete',
            f"Are you sure you want to delete account for {account.get('gmail', 'this account')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.accounts = [acc for acc in self.accounts if acc['id'] != account['id']]
            AccountManager.save_accounts(self.accounts)
            self.load_data()
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self,
            'Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    """Main entry point"""
    # Create empty data file if it doesn't exist
    if not os.path.exists(DATA_FILE):
        AccountManager.save_accounts([])
    
    app = QApplication(sys.argv)
    app.setApplicationName('Bybit Account Manager')

    # Set app-level icon (taskbar + alt-tab)
    app_icon_path = os.path.join(_ASSETS_DIR, 'Bybit.png')
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
