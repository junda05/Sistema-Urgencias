from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QStyledItemDelegate, QToolTip,
                           QHeaderView, QAbstractItemView, QStyleOptionViewItem)
from PyQt5.QtCore import Qt, QTimer, QRectF, QSize, QEvent
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont
from backend.database import PatientModel

class StatusCircleDelegate(QStyledItemDelegate):
    """Delegate that renders statuses as colored circles with alarms."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.patient_model = PatientModel()
        self.colors = self.patient_model.get_colors()
        self.circle_size = 50
        self.alarm_cells = set()
        self.disposition_alarm_cells = set()
        self.blink_state = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_blink)
        self.timer.start(500)

    def toggle_blink(self):
        """Toggles the blinking state for cells with an alarm."""
        self.blink_state = not self.blink_state
        if self.alarm_cells:
            for row, col in self.alarm_cells:
                self.parent().update(self.parent().model().index(row, col))
        if self.disposition_alarm_cells:
            for row, col in self.disposition_alarm_cells:
                self.parent().update(self.parent().model().index(row, col))

    def set_alarm_cells(self, alarm_cells):
        """Defines which cells have a standard alarm."""
        self.alarm_cells = alarm_cells

    def set_disposition_alarm_cells(self, disposition_alarm_cells):
        """Defines which cells have a disposition alarm."""
        self.disposition_alarm_cells = disposition_alarm_cells

    def sizeHint(self, option, index):
        """Recommended size for the cells containing circles."""
        return QSize(self.circle_size + 10, self.circle_size + 10)  # +10 for padding

    def paint(self, painter, option, index):
        """Draws the cell content according to its status."""
        text = index.data(Qt.DisplayRole)
        row = index.row()
        col = index.column()

        is_alarm = (row, col) in self.alarm_cells
        is_disposition_alarm = (row, col) in self.disposition_alarm_cells

        # Check whether it is a triage number or a status with a defined color
        if text in self.colors or text in ["2", "3"]:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)

            if is_alarm and self.blink_state:
                color = QColor("#FFA500")  # Orange for a normal alarm
            elif is_disposition_alarm and self.blink_state:
                color = QColor("#9370DB")  # Soft purple for an observation alarm
            else:
                # Get the color from the model; works for normal statuses as well as triage 2 and 3
                color = QColor(self.colors.get(text, "#CCCCCC"))  # Default gray color if it does not exist

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))

            x = option.rect.x() + (option.rect.width() - self.circle_size) / 2
            y = option.rect.y() + (option.rect.height() - self.circle_size) / 2

            # Draw a circle for normal statuses
            if not is_disposition_alarm:
                painter.drawEllipse(QRectF(x, y, self.circle_size, self.circle_size))

                # Draw the number inside the circle for triage 2 and 3
                if text in ["1", "2", "3", "4", "5"]:
                    # Set the text color (white for better contrast)
                    painter.setPen(Qt.white)
                    # Set the font for the number
                    font = QFont()
                    font.setPointSize(20)
                    font.setBold(True)
                    painter.setFont(font)
                    # Draw the text centered inside the circle
                    painter.drawText(QRectF(x, y, self.circle_size, self.circle_size),
                                    Qt.AlignCenter, text)
            else:
                # For a disposition alarm, fill the whole cell
                if self.blink_state:
                    # Fill the whole cell with a semi-transparent purple
                    painter.setBrush(QBrush(QColor(147, 112, 219, 100)))  # Semi-transparent purple
                    painter.drawRect(option.rect)

                # Then draw the main circle
                painter.setBrush(QBrush(color))
                painter.drawEllipse(QRectF(x, y, self.circle_size, self.circle_size))

                # Draw the number inside the circle for triage 2 and 3 even when there is an alarm
                if text in ["1", "2", "3", "4", "5"]:
                    painter.setPen(Qt.white)
                    font = QFont()
                    font.setPointSize(20)
                    font.setBold(True)
                    painter.setFont(font)
                    painter.drawText(QRectF(x, y, self.circle_size, self.circle_size),
                                    Qt.AlignCenter, text)

            painter.restore()
        else:
            # For texts with no associated color that may still have an alarm (such as "Observation")
            if is_disposition_alarm and text == "Observation":
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing)

                # Draw a background for the whole cell with a pulsing effect
                if self.blink_state:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(147, 112, 219, 80)))  # Semi-transparent purple
                    painter.drawRect(option.rect)
                else:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(147, 112, 219, 30)))  # Very soft purple when not pulsing
                    painter.drawRect(option.rect)

                # Draw the text with a colored outline
                font = painter.font()
                font.setBold(True)
                painter.setFont(font)

                if self.blink_state:
                    painter.setPen(QColor("#8A2BE2"))  # More intense purple for the text
                else:
                    painter.setPen(QColor("#666666"))  # Normal gray for non-pulsing text

                painter.drawText(option.rect, Qt.AlignCenter, text)
                painter.restore()
            else:
                super().paint(painter, option, index)

    def helpEvent(self, event, view, option, index):
        """Shows tooltips when hovering the mouse over specific cells."""
        if event.type() == QEvent.ToolTip:
            text = index.data(Qt.DisplayRole)
            if text in self.colors or text in ["2", "3"]:  # We add triage 2 and 3 for tooltips
                QToolTip.showText(event.globalPos(), text, view)
                return True
        return super().helpEvent(event, view, option, index)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseMove:
            # If we are over the Labs column (index 4)
            if index.column() == 4:  # 4 is the "Labs" column
                # Get the patient ID from the current row
                patient_id = model.index(index.row(), 13).data()  # Assuming the ID is in column 13
                if patient_id:
                    try:
                        # Get the patient's labs
                        patient_model = PatientModel()
                        labs = patient_model.get_patient_labs(patient_id)
                        patient_model.close_db()

                        if labs:
                            # Build the tooltip
                            tooltip_text = "<b>Assigned labs:</b><br>"
                            for code, name, status in labs:
                                tooltip_text += f"• {code} - {name}: <i>{status}</i><br>"
                            QToolTip.showText(event.globalPos(), tooltip_text)
                            return True
                    except Exception as e:
                        print(f"Error showing labs tooltip: {str(e)}")

        return super().editorEvent(event, model, option, index)

class TextDelegate(QStyledItemDelegate):
    """Delegate that shows tooltips on text cells."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.patient_model = PatientModel()

    def paint(self, painter, option, index):
        # Make a copy of the option so we can modify it
        opt = QStyleOptionViewItem(option)

        # Check which column we're in
        if index.column() == 8:  # Pending Tasks column (index 8)
            # Get cell text content
            text = index.data(Qt.DisplayRole) or ""

            # Check if the pending tasks contain labs or imaging references
            if "Labs pending:" in text or "Imaging pending:" in text:
                # Keep left alignment for lab and imaging pending tasks
                opt.displayAlignment = Qt.AlignLeft | Qt.AlignVCenter
            else:
                # Center other pending task text
                opt.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter
        elif index.column() == 9:  # Disposition column (index 9)
            # Center text for the disposition column
            opt.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter
        else:
            # Center text for all other columns
            opt.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter

        # Call the base implementation with our modified options
        super().paint(painter, opt, index)

    def helpEvent(self, event, view, option, index):
        """Customize tooltips to show cell content with better styling"""
        if not event or not view:
            return False

        if event.type() == QEvent.ToolTip:
            # Get the data to display in tooltip
            text = index.data(Qt.DisplayRole)

            # Identify whether we are in the pending tasks column (index 8)
            if index.column() == 8 and text:
                # Detect whether there are pending labs or imaging studies in the text
                pending_labs = set()  # Use a set to avoid duplicates
                pending_imgs = set()  # Use a set to avoid duplicates

                # Debug: print the full text of the cell

                # Check whether there is a pending labs section
                if "Labs pending:" in text:
                    labs_part = text.split("Labs pending:")[1]
                    # If imaging studies follow, cut before the pending imaging section
                    if "Imaging pending:" in labs_part:
                        labs_part = labs_part.split("Imaging pending:")[0]
                    # Clean up and split the labs
                    labs_items = [lab.strip() for lab in labs_part.split(",")]
                    # Add unique items to the set
                    for lab in labs_items:
                        if lab and not lab.startswith("Imaging pending:"):
                            pending_labs.add(lab)

                # Check whether there is a pending imaging section
                if "Imaging pending:" in text:
                    img_part = text.split("Imaging pending:")[1]
                    # Clean up and split the imaging studies
                    img_items = [img.strip() for img in img_part.split(",")]
                    # Add unique items to the set
                    for img in img_items:
                        if img:
                            pending_imgs.add(img)

                # If we found labs or imaging studies, build a custom tooltip
                if pending_labs or pending_imgs:
                    # Build the HTML for the tooltip
                    tooltip_html = ""

                    # Add the labs section if any exist
                    if pending_labs:
                        tooltip_html += "<b>Labs:</b><br>"
                        for lab in sorted(pending_labs):  # Sort for consistency
                            tooltip_html += f"• {lab}<br>"

                        # Add spacing between sections if there are imaging studies as well
                        if pending_imgs:
                            tooltip_html += "<br>"

                    # Add the diagnostic imaging section if any exist
                    if pending_imgs:
                        tooltip_html += "<b>Diagnostic imaging:</b><br>"
                        for img in sorted(pending_imgs):  # Sort for consistency
                            tooltip_html += f"• {img}<br>"

                    # Debug: show the final tooltip HTML

                    # Show the custom tooltip
                    QToolTip.setFont(QFont("Segoe UI", 10))
                    QToolTip.showText(event.globalPos(), tooltip_html, view)
                    return True

            # For any other column, or when there are no labs/imaging studies, show the standard tooltip
            if text:
                QToolTip.setFont(QFont("Segoe UI", 10))
                QToolTip.showText(event.globalPos(), text, view)
                return True

        return super().helpEvent(event, view, option, index)

    def editorEvent(self, event, model, option, index):
        # Check whether we are over the pending tasks column and there is a mouse event
        if index.column() == 8 and event.type() == QEvent.MouseMove:
            # Get the patient ID from the current row
            patient_id = model.index(index.row(), 13).data()  # Assuming the ID is in column 13

            if patient_id:
                try:
                    # Directly get the labs and imaging studies assigned to the patient
                    labs = self.patient_model.get_patient_labs(patient_id)
                    imgs = self.patient_model.get_patient_imaging(patient_id)

                    # Debug: show the labs and imaging studies retrieved from the database

                    # Filter by status to show only the pending ones
                    pending_labs = [lab for lab in labs if lab[2] in ["Not started", "Awaiting results"]]
                    pending_imgs = [img for img in imgs if img[2] in ["Not started", "Awaiting results"]]

                    # Debug: show the pending labs and imaging studies

                    self.patient_model.close_db()

                    # If there are pending labs or imaging studies, show a detailed tooltip
                    if pending_labs or pending_imgs:
                        tooltip_html = ""

                        # Add the labs section if any exist
                        if pending_labs:
                            tooltip_html += "<b>Labs:</b><br>"
                            # Sort the labs by name for a consistent presentation
                            sorted_labs = sorted(pending_labs, key=lambda lab: lab[1])
                            for code, name, _ in sorted_labs:
                                tooltip_html += f"• {name}<br>"

                            # Add spacing between sections if there are imaging studies as well
                            if pending_imgs:
                                tooltip_html += "<br>"

                        # Add the diagnostic imaging section if any exist
                        if pending_imgs:
                            tooltip_html += "<b>Diagnostic imaging:</b><br>"
                            # Sort the imaging studies by name for a consistent presentation
                            sorted_imgs = sorted(pending_imgs, key=lambda img: img[1])
                            for code, name, _ in sorted_imgs:
                                tooltip_html += f"• {name}<br>"

                        # Debug: show the final tooltip HTML

                        # Show the custom tooltip
                        QToolTip.setFont(QFont("Segoe UI", 10))
                        QToolTip.showText(event.globalPos(), tooltip_html)
                        return True

                except Exception as e:
                    print(f"Error showing the detailed tooltip for pending tasks: {str(e)}")

        return super().editorEvent(event, model, option, index)

class CustomColumnHeader(QTableWidgetItem):
    """Custom item used to show colored circles in cells."""
    def __init__(self, text, state=None):
        super().__init__(text)
        self.state = state
        self.patient_model = PatientModel()
        self.colors = self.patient_model.get_colors()
        self.setData(Qt.DisplayRole, state)

def configure_standard_table(table, headers, delegate_columns=None, text_delegate_columns=None,
                           font_name="ABeeZee", row_height=70):
    """
    Configures a table with the standard style and delegates.

    Args:
        table: QTableWidget to configure
        headers: List of column headers
        delegate_columns: Dictionary of {column_name: delegate} for special columns
        text_delegate_columns: List of column names to apply TextDelegate to
        font_name: Name of the font to use
        row_height: Height of the rows
    """
    # Basic configuration
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)

    # Styles and behavior
    table.setAlternatingRowColors(False)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.clearSelection()
    table.setCurrentCell(-1, -1)

    # Font
    font = QFont(font_name)
    table.setFont(font)

    # Bold headers
    header_font = QFont(font_name)
    header_font.setBold(True)
    table.horizontalHeader().setFont(header_font)

    # Text wrapping
    table.setWordWrap(True)

    # Smooth scrolling
    table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

    # Apply delegates if provided
    if delegate_columns:
        for column_name, delegate in delegate_columns.items():
            if column_name in headers:
                col_index = headers.index(column_name)
                table.setItemDelegateForColumn(col_index, delegate)

    # Apply the text delegate to the specified columns
    if text_delegate_columns:
        text_delegate = TextDelegate(table)
        for column_name in text_delegate_columns:
            if column_name in headers:
                col_index = headers.index(column_name)
                table.setItemDelegateForColumn(col_index, text_delegate)

    # Uniform row height
    for row in range(table.rowCount()):
        table.setRowHeight(row, row_height)

def configure_column_widths(table, headers, special_columns=None):
    """
    Configures the column widths proportionally, with some special columns.

    Args:
        table: QTableWidget to configure
        headers: List of column headers
        special_columns: Dictionary of {column_name: width_factor} for columns with a special width
    """
    # Save the current resize mode of the columns
    current_modes = []
    for col in range(table.columnCount()):
        current_modes.append(table.horizontalHeader().sectionResizeMode(col))

    # Temporarily set every column to stretch mode
    for col in range(table.columnCount()):
        table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

    # Update the table size so that it adjusts correctly
    table.updateGeometry()
    table.viewport().updateGeometry()

    # Calculate widths based on the current table size
    table_width = table.width()
    column_count = len(headers)
    standard_column_width = table_width / column_count

    # Special columns with a proportional width
    if special_columns:
        for column_name, factor in special_columns.items():
            if column_name in headers:
                column_index = headers.index(column_name)
                # Switch to fixed mode for specific columns
                table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.Fixed)
                # Set the specific width
                table.setColumnWidth(column_index, int(standard_column_width * factor))

    # Ensure the changes are visible immediately
    table.horizontalHeader().update()

    return table