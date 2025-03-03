from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                            QPushButton, QLabel, QComboBox, QDoubleSpinBox,
                            QTextEdit, QTableWidget, QTableWidgetItem, QSpinBox)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor  # Add this import
from simulation import market_state
from simulation.market_simulation import market_session
import time

GROUP_BOX_STYLE = """
QGroupBox {
    font-weight: bold;
    border: 2px solid gray;
    border-radius: 5px;
    margin-top: 1ex;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 3px;
}
"""

BUTTON_STYLE = """
QPushButton {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    font-size: 16px;
    margin: 4px 2px;
    border-radius: 8px;
}
QPushButton:hover {
    background-color: #45a049;
}
QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}
"""

STATUS_LABEL_STYLE = """
QLabel[status="info"] {
    color: blue;
    font-weight: bold;
}
"""

INPUT_STYLE = """
QComboBox, QDoubleSpinBox {
    padding: 5px;
    border: 1px solid gray;
    border-radius: 5px;
}
"""

TABLE_STYLE = """
QTableWidget {
    border: 1px solid gray;
    border-radius: 5px;
}
QHeaderView::section {
    background-color: lightgray;
    padding: 4px;
    border: 1px solid gray;
}
"""

COLORS = {
    'background': '#f0f0f0',
    'text': '#333333',
    'border': '#cccccc'
}

class MarketControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        # Create member variables first
        self.create_controls()
        self.init_ui()
        self.setup_timer()
        # Initialize button states
        self.update_button_states(False)

    def create_controls(self):
        """Create all control widgets as class members"""
        # Session control buttons
        self.start_session_btn = QPushButton("Start Session")
        self.end_session_btn = QPushButton("End Session")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.session_status_label = QLabel("Session: Not Started")

        # Override controls
        self.stock_selector = QComboBox()
        self.price_spinner = QDoubleSpinBox()
        self.override_btn = QPushButton("Override Price")  # Changed name to override_btn
        
        # Price display
        self.price_table = QTableWidget()
        self.log_text = QTextEdit()

        # Configure controls
        self.price_spinner.setRange(0.01, 100000.00)  # Increased range
        self.price_spinner.setDecimals(2)
        self.price_spinner.setSingleStep(0.10)  # More precise control
        self.price_spinner.setPrefix("$")
        self.price_spinner.setKeyboardTracking(False)  # Only update on enter/finish editing
        self.log_text.setReadOnly(True)

        # Connect signals
        self.start_session_btn.clicked.connect(self.start_session)
        self.end_session_btn.clicked.connect(self.end_session)
        self.pause_btn.clicked.connect(self.pause_session)
        self.resume_btn.clicked.connect(self.resume_session)
        self.override_btn.clicked.connect(self.override_price)  # Connect override button

        # Add signal connection for stock selection
        self.stock_selector.currentIndexChanged.connect(self.update_price_spinner_range)

        # Add trade order controls with separate stock selector
        self.team_selector = QComboBox()
        self.team_selector.addItems([f"Team {i+1}" for i in range(market_state.TEAM_COUNT)])
        
        self.order_type = QComboBox()
        self.order_type.addItems(["buy", "sell"])
        
        # Create separate stock selector for team orders
        self.team_order_stock_selector = QComboBox()
        
        self.quantity_spinner = QSpinBox()
        self.quantity_spinner.setRange(1, 10000)
        self.quantity_spinner.setValue(100)
        
        self.place_order_btn = QPushButton("Place Order")
        self.place_order_btn.clicked.connect(self.place_team_order)

        # Add price manipulation controls
        self.price_change_spinner = QDoubleSpinBox()
        self.price_change_spinner.setRange(-20.0, 20.0)  # Wider range: ±20%
        self.price_change_spinner.setDecimals(2)
        self.price_change_spinner.setValue(0.0)
        self.price_change_spinner.setSingleStep(0.5)  # Finer step control
        self.price_change_spinner.setSuffix("%")
        
        self.apply_change_btn = QPushButton("Apply Price Change")
        self.apply_change_btn.clicked.connect(self.apply_price_change)
        self.apply_change_btn.setStyleSheet(BUTTON_STYLE)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Session Controls with enhanced styling
        session_group = QGroupBox("Session Controls")
        session_group.setStyleSheet(GROUP_BOX_STYLE)
        session_layout = QHBoxLayout()
        session_layout.setSpacing(15)
        session_layout.setContentsMargins(15, 20, 15, 20)

        # Style the status label
        self.session_status_label.setProperty('status', 'info')
        self.session_status_label.setStyleSheet(STATUS_LABEL_STYLE)
        
        # Style the control buttons
        control_buttons = [self.start_session_btn, self.end_session_btn,
                          self.pause_btn, self.resume_btn]
        
        for btn in control_buttons:
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setMinimumWidth(120)

        session_layout.addWidget(self.start_session_btn)
        session_layout.addWidget(self.end_session_btn)
        session_layout.addWidget(self.pause_btn)
        session_layout.addWidget(self.resume_btn)
        session_layout.addWidget(self.session_status_label)

        session_group.setLayout(session_layout)
        layout.addWidget(session_group)

        # Update button initial states
        self.update_button_states(False)

        # Override Controls with enhanced styling
        override_group = QGroupBox("Manual Price Override")
        override_group.setStyleSheet(GROUP_BOX_STYLE)
        override_layout = QHBoxLayout()
        override_layout.setSpacing(15)
        override_layout.setContentsMargins(15, 20, 15, 20)

        self.stock_selector.setStyleSheet(INPUT_STYLE)
        self.price_spinner.setStyleSheet(INPUT_STYLE)
        self.override_btn.setStyleSheet(BUTTON_STYLE)

        override_layout.addWidget(QLabel("Stock:"))
        override_layout.addWidget(self.stock_selector)
        override_layout.addWidget(QLabel("New Price:"))
        override_layout.addWidget(self.price_spinner)
        override_layout.addWidget(self.override_btn)  # Use the correct button name

        override_group.setLayout(override_layout)
        layout.addWidget(override_group)

        # Update Trade Order section with separate stock selector
        trade_group = QGroupBox("Place Team Orders")
        trade_group.setStyleSheet(GROUP_BOX_STYLE)
        trade_layout = QHBoxLayout()
        
        # Apply style to new stock selector
        self.team_order_stock_selector.setStyleSheet(INPUT_STYLE)
        
        trade_layout.addWidget(QLabel("Team:"))
        trade_layout.addWidget(self.team_selector)
        trade_layout.addWidget(QLabel("Action:"))
        trade_layout.addWidget(self.order_type)
        trade_layout.addWidget(QLabel("Stock:"))
        trade_layout.addWidget(self.team_order_stock_selector)  # Use separate selector
        trade_layout.addWidget(QLabel("Quantity:"))
        trade_layout.addWidget(self.quantity_spinner)
        trade_layout.addWidget(self.place_order_btn)
        
        trade_group.setLayout(trade_layout)
        layout.addWidget(trade_group)

        # Add Price Manipulation section after Override Controls
        manipulation_group = QGroupBox("Price Manipulation")
        manipulation_group.setStyleSheet(GROUP_BOX_STYLE)
        manipulation_layout = QHBoxLayout()
        manipulation_layout.setSpacing(15)
        manipulation_layout.setContentsMargins(15, 20, 15, 20)

        self.price_change_spinner.setStyleSheet(INPUT_STYLE)
        
        manipulation_layout.addWidget(QLabel("Stock:"))
        manipulation_layout.addWidget(self.stock_selector)
        manipulation_layout.addWidget(QLabel("Price Change:"))
        manipulation_layout.addWidget(self.price_change_spinner)
        manipulation_layout.addWidget(self.apply_change_btn)

        manipulation_group.setLayout(manipulation_layout)
        layout.addWidget(manipulation_group)

        # Stock Price Display
        price_group = QGroupBox("Current Stock Prices")
        price_layout = QVBoxLayout()
        self.price_table = QTableWidget()
        self.price_table.setColumnCount(3)
        self.price_table.setHorizontalHeaderLabels(["Stock", "Price", "Available Quantity"])
        price_layout.addWidget(self.price_table)
        price_group.setLayout(price_layout)
        layout.addWidget(price_group)

        # Enhanced table styling
        self.price_table.setStyleSheet(TABLE_STYLE)
        self.price_table.horizontalHeader().setStretchLastSection(True)
        self.price_table.verticalHeader().setVisible(False)
        self.price_table.setShowGrid(False)

        # Action Log
        log_group = QGroupBox("Action Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Enhanced log text styling
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
            }}
        """)

        self.setLayout(layout)
        self.update_stock_list()
        self.update_session_status()

    def setup_timer(self):
        """Setup timers for updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_price_display)
        self.update_timer.start(1000)  # Update every second

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_session_status)
        self.status_timer.start(500)  # Update status more frequently

    def update_stock_list(self):
        """Update all stock selectors"""
        current_stocks = market_state.stock_prices.keys()
        
        # Update main stock selector
        self.stock_selector.clear()
        self.stock_selector.addItems(current_stocks)
        
        # Update team order stock selector
        self.team_order_stock_selector.clear()
        self.team_order_stock_selector.addItems(current_stocks)

    def update_price_display(self):
        """Enhanced price display with more stock information"""
        self.price_table.setColumnCount(5)  # Increased columns
        self.price_table.setHorizontalHeaderLabels([
            "Symbol (Name)", "Sector", "Price", "Change %", "Available"
        ])
        
        stocks = market_state.stock_prices.keys()
        self.price_table.setRowCount(len(stocks))
        
        for row, symbol in enumerate(stocks):
            info = market_state.get_stock_info(symbol)
            if info:
                # Symbol and name
                self.price_table.setItem(row, 0, 
                    QTableWidgetItem(f"{symbol} ({info['name']})"))
                
                # Sector
                self.price_table.setItem(row, 1,
                    QTableWidgetItem(info['sector']))
                
                # Price
                self.price_table.setItem(row, 2,
                    QTableWidgetItem(f"${info['current_price']:.2f}"))
                
                # Change %
                change_item = QTableWidgetItem(f"{info['change']:+.2f}%")
                change_item.setForeground(
                    QColor('green') if info['change'] >= 0 else QColor('red'))
                self.price_table.setItem(row, 3, change_item)
                
                # Available quantity
                self.price_table.setItem(row, 4,
                    QTableWidgetItem(f"{info['available']:,}"))
        
        self.price_table.resizeColumnsToContents()
        self.price_table.viewport().update()

    def update_price_spinner_range(self):
        """Update price spinner range based on selected stock"""
        stock = self.stock_selector.currentText()
        if stock in market_state.stock_prices:
            current_price = market_state.stock_prices[stock]
            # Set range to 50% below and 200% above current price
            min_price = max(0.01, current_price * 0.5)
            max_price = current_price * 3.0
            self.price_spinner.setRange(min_price, max_price)
            self.price_spinner.setValue(current_price)

    def override_price(self):
        """Enhanced manual price override with validation and feedback"""
        if not market_session.session_active:
            self.log_text.append("Cannot override price: No active session")
            return
            
        stock = self.stock_selector.currentText()
        if not stock:
            self.log_text.append("Error: No stock selected")
            return
            
        new_price = self.price_spinner.value()
        current_price = market_state.stock_prices.get(stock, 0)
        
        # Calculate percentage change
        percent_change = ((new_price - current_price) / current_price) * 100
        
        # Validate price change
        if abs(percent_change) > 50:  # Limit to 50% change
            self.log_text.append(f"Warning: Price change of {percent_change:.1f}% exceeds 50% limit")
            return
        
        # Confirm large changes
        if abs(percent_change) > 20:
            msg = (f"Warning: Large price change of {percent_change:.1f}%\n"
                  f"Current: ${current_price:.2f} → New: ${new_price:.2f}\n"
                  f"Do you want to proceed?")
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, 'Confirm Price Override', msg,
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # Update the market state with validation
        if market_state.manual_override_price(stock, new_price):
            log_entry = (f"Manual override: {stock} price changed from "
                        f"${current_price:.2f} to ${new_price:.2f} ({percent_change:+.2f}%)")
            self.log_text.append(log_entry)
            # Force immediate update of price display
            self.update_price_display()
        else:
            self.log_text.append(f"Failed to override price for {stock}")

    def start_session(self):
        """Start session without resetting market state"""
        try:
            if market_session.session_active:
                self.log_text.append("Error: Session already active")
                return False

            # Remove market state initialization - preserve existing holdings
            if market_session.start_session():
                self.log_text.append("New trading session started successfully")
                self.update_button_states(True)
                self.update_session_status()
                # Update displays immediately
                self.update_price_display()
                self.update_stock_list()
                return True
            else:
                self.log_text.append("Failed to start session")
                return False
                
        except Exception as e:
            self.log_text.append(f"Error starting session: {str(e)}")
            return False

    def end_session(self):
        if market_session.end_session():
            self.log_text.append("Trading session ended")
            self.update_button_states(False)
            self.update_session_status()
        else:
            self.log_text.append("Failed to end session")

    def pause_session(self):
        if market_session.pause():
            self.log_text.append("Trading session paused")
            self.update_button_states(True, True)
            self.update_session_status()
        else:
            self.log_text.append("Failed to pause session")

    def resume_session(self):
        if market_session.resume():
            self.log_text.append("Trading session resumed")
            self.update_button_states(True, False)
            self.update_session_status()
        else:
            self.log_text.append("Failed to resume session")

    def update_session_status(self):
        """Update session status with time remaining"""
        status = market_session.get_session_status()
        status_text = f"Session: {status['current_session']}/{status['max_sessions']}"
        
        if status['is_active']:
            if status['is_paused']:
                status_text += f" (Paused - {status['time_remaining']} remaining)"
            else:
                status_text += f" (Active - {status['time_remaining']} remaining)"
        else:
            status_text += " (Inactive)"
            
        self.session_status_label.setText(status_text)
        self.update_button_states(status['is_active'], status['is_paused'])

    def update_button_states(self, is_session_active, is_paused=False):
        """Update button states based on session status"""
        self.start_session_btn.setEnabled(not is_session_active)
        self.end_session_btn.setEnabled(is_session_active)
        self.pause_btn.setEnabled(is_session_active and not is_paused)
        self.resume_btn.setEnabled(is_session_active and is_paused)
        # Always enable trading buttons
        self.override_btn.setEnabled(True)
        self.place_order_btn.setEnabled(True)
        self.apply_change_btn.setEnabled(True)

    def place_team_order(self):
        """Enhanced team order placement with no session validation"""
        team_id = int(self.team_selector.currentText().split()[-1]) - 1
        stock = self.team_order_stock_selector.currentText()
        quantity = self.quantity_spinner.value()
        order_type = self.order_type.currentText()
        
        # Remove session check
        # Validate quantity
        if quantity <= 0:
            self.log_text.append("Error: Quantity must be positive")
            return
            
        # Validate against available quantity for buys
        if order_type == "buy" and quantity > market_state.available_quantities.get(stock, 0):
            self.log_text.append(f"Error: Insufficient {stock} available in market")
            return
        
        order = {
            'stock': stock,
            'quantity': quantity,
            'type': order_type,
            'timestamp': time.time()
        }
        
        # Get current price for logging
        current_price = market_state.stock_prices.get(stock, 0)
        estimated_value = current_price * quantity
        
        # Log attempt
        self.log_text.append(f"Attempting {order_type} order: {quantity} {stock} at ~${current_price:.2f} (Est. ${estimated_value:.2f})")
        
        success = market_state.process_market_order(team_id, order)
        
        if success:
            self.log_text.append(f"Order executed for Team {team_id}")
            # Show updated portfolio value
            portfolio = market_state.get_team_portfolio(team_id)
            self.log_text.append(f"Team {team_id} new portfolio value: ${portfolio['total_value']:,.2f}")
            # Reset quantity spinner after successful order
            self.quantity_spinner.setValue(100)
        else:
            self.log_text.append(f"Order failed for Team {team_id}")

    def apply_price_change(self):
        """Apply percentage price change to selected stock with improved validation"""
        if not market_session.session_active:
            self.log_text.append("Cannot manipulate price: No active session")
            return
            
        stock = self.stock_selector.currentText()
        percent_change = self.price_change_spinner.value() / 100.0
        
        # Add validation for maximum single change
        if abs(percent_change) > 0.20:  # 20% maximum change
            self.log_text.append("Warning: Maximum allowed change is ±20%")
            return
            
        current_price = market_state.stock_prices.get(stock, 0)
        new_price = current_price * (1 + percent_change)
        
        # Ensure minimum price
        if new_price < 0.01:
            self.log_text.append("Error: Price cannot go below $0.01")
            return
        
        if market_state.update_stock_price(stock, new_price):
            log_entry = f"Price manipulation: {stock} changed by {percent_change*100:+.2f}% from ${current_price:.2f} to ${new_price:.2f}"
            self.log_text.append(log_entry)
            self.update_price_display()
            # Reset spinner to 0 after successful change
            self.price_change_spinner.setValue(0.0)
        else:
            self.log_text.append(f"Failed to manipulate price for {stock}")
