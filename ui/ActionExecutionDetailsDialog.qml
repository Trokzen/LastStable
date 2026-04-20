// ui/ActionExecutionDetailsDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5
import QtQuick.Dialogs 6.5

Popup {
    id: actionDetailsDialog
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    width: parent.width * 0.98
    height: parent.height * 0.95
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // --- Свойства ---
    property int executionId: -1
    property int currentActionIndex: -1
    property int totalActions: 0
    property bool autoSwitch: false
    property bool isOverdue: false
    property string currentStatus: "pending"

    // --- Таймеры ---
    Timer {
        id: countdownTimer
        interval: 1000
        repeat: true
        running: true
        onTriggered: {
            updateCountdown()
            checkOverdue()
        }
    }

    Timer {
        id: overduePulseTimer
        interval: 800
        repeat: true
        running: actionDetailsDialog.isOverdue
    }

    // --- Модели данных ---
    ListModel {
        id: reportMaterialsModel
    }
    // Используем JS массив вместо ListModel для сохранения вложенных списков (файлов организаций)
    property var allOrganizations: []
    // --- ---

    // --- Функции ---
    
    // Получаем текущее местное время из appData
    function getLocalNow() {
        var dateStr = appData.localDate || ""
        var timeStr = appData.localTime || ""
        
        if (!dateStr || !timeStr) return new Date() // Фоллбэк на системное, если данных нет

        var dateParts = dateStr.split('.')
        var timeParts = timeStr.split(':')
        
        if (dateParts.length === 3 && timeParts.length === 3) {
            var day = parseInt(dateParts[0], 10)
            var month = parseInt(dateParts[1], 10) - 1
            var year = parseInt(dateParts[2], 10)
            var hours = parseInt(timeParts[0], 10)
            var minutes = parseInt(timeParts[1], 10)
            var seconds = parseInt(timeParts[2], 10)
            return new Date(year, month, day, hours, minutes, seconds)
        }
        return new Date()
    }

    function updateCountdown() {
        var now = getLocalNow()
        var startTimeText = calculatedStartTimeLabel.text
        var endTimeText = calculatedEndTimeLabel.text

        // Проверяем, задано ли время начала
        if (!startTimeText || startTimeText === "Не задано" || startTimeText === "—") {
            remainingTimeLabel.text = "—"
            remainingTimeLabel.color = "#95a5a6"
            return
        }

        // Проверяем, задано ли время окончания
        if (!endTimeText || endTimeText === "Не задано") {
            remainingTimeLabel.text = "—"
            remainingTimeLabel.color = "#95a5a6"
            return
        }

        // Парсим дату начала
        var startParts = startTimeText.match(/(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2}):(\d{2})/)
        if (!startParts) {
            remainingTimeLabel.text = "—"
            remainingTimeLabel.color = "#95a5a6"
            return
        }

        var startDate = new Date(parseInt(startParts[3]), parseInt(startParts[2]) - 1, parseInt(startParts[1]),
                                 parseInt(startParts[4]), parseInt(startParts[5]), parseInt(startParts[6]))

        // Если время начала еще не наступило - таймер не идет
        if (now < startDate) {
            remainingTimeLabel.text = "⏸ Ожидание"
            remainingTimeLabel.color = "#3498db"
            return
        }

        // Парсим дату окончания
        var endParts = endTimeText.match(/(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2}):(\d{2})/)
        if (!endParts) {
            remainingTimeLabel.text = "—"
            remainingTimeLabel.color = "#95a5a6"
            return
        }

        var endDate = new Date(parseInt(endParts[3]), parseInt(endParts[2]) - 1, parseInt(endParts[1]),
                               parseInt(endParts[4]), parseInt(endParts[5]), parseInt(endParts[6]))
        var diff = endDate - now

        if (diff <= 0) {
            remainingTimeLabel.text = "00:00:00"
            remainingTimeLabel.color = "#e74c3c"
        } else {
            var hours = Math.floor(diff / 3600000)
            var minutes = Math.floor((diff % 3600000) / 60000)
            var seconds = Math.floor((diff % 60000) / 1000)
            remainingTimeLabel.text = String(hours).padStart(2, '0') + ":" +
                                      String(minutes).padStart(2, '0') + ":" +
                                      String(seconds).padStart(2, '0')
            remainingTimeLabel.color = diff <= 300000 ? "#f39c12" : "#27ae60"
        }
    }

    function checkOverdue() {
        var now = getLocalNow()
        var endTimeText = calculatedEndTimeLabel.text
        if (!endTimeText || endTimeText === "Не задано") return

        var endParts = endTimeText.match(/(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2}):(\d{2})/)
        if (!endParts) return

        var endDate = new Date(parseInt(endParts[3]), parseInt(endParts[2]) - 1, parseInt(endParts[1]),
                               parseInt(endParts[4]), parseInt(endParts[5]), parseInt(endParts[6]))
        actionDetailsDialog.isOverdue = now > endDate

        // Автопереключение
        if (actionDetailsDialog.isOverdue && actionDetailsDialog.autoSwitch) {
            switchToNext()
        }
    }

    function switchToNext() {
        if (actionDetailsDialog.currentActionIndex < actionDetailsDialog.totalActions - 1) {
            actionDetailsDialog.currentActionIndex++
            loadActionData()
        }
    }

    function switchToPrevious() {
        if (actionDetailsDialog.currentActionIndex > 0) {
            actionDetailsDialog.currentActionIndex--
            loadActionData()
        }
    }

    function loadActionData() {
        if (actionDetailsDialog.executionId <= 0 || actionDetailsDialog.currentActionIndex < 0) return

        var actions = appData.getActionExecutionsByExecutionId(actionDetailsDialog.executionId)
        if (!actions || actionDetailsDialog.currentActionIndex >= actions.length) return

        var action = actions[actionDetailsDialog.currentActionIndex]
        actionDetailsDialog.totalActions = actions.length

        // Название
        var actionNum = actionDetailsDialog.currentActionIndex + 1
        actionNameLabel.text = "Мероприятие №" + actionNum + ": " + (action.snapshot_description || "Без названия")

        // Время начала
        calculatedStartTimeLabel.text = action.calculated_start_time ? formatDateTime(action.calculated_start_time) : "Не задано"

        // Время окончания
        calculatedEndTimeLabel.text = action.calculated_end_time ? formatDateTime(action.calculated_end_time) : "Не задано"

        // Технический текст (из snapshot_technical_text)
        if (action.snapshot_technical_text && action.snapshot_technical_text.trim()) {
            technicalTextContent.text = action.snapshot_technical_text
        } else {
            technicalTextContent.text = "Нет технического текста"
        }

        // Статус
        var statusText = ""
        var statusColor = "#95a5a6"
        actionDetailsDialog.currentStatus = action.status || "pending"
        
        if (action.status === "completed") {
            statusText = "✅ Выполнено"
            statusColor = "#27ae60"
        } else if (action.status === "in_progress") {
            statusText = "🔄 В процессе"
            statusColor = "#f39c12"
        } else if (action.status === "pending") {
            statusText = "⏸ Ожидает"
            statusColor = "#3498db"
        } else if (action.status === "skipped") {
            statusText = "❌ Пропущено"
            statusColor = "#e74c3c"
        }
        statusLabel.text = statusText
        statusRectangle.color = statusColor

        // Отчётные материалы
        reportMaterialsModel.clear()
        if (action.snapshot_report_materials) {
            var materials = action.snapshot_report_materials.split('\n')
            for (var i = 0; i < materials.length; i++) {
                if (materials[i].trim()) {
                    reportMaterialsModel.append({ "path": materials[i].trim() })
                }
            }
        }

        // Кому доложено
        reportedToHidden.text = action.reported_to || "—"

        // Справочные материалы организаций
        loadOrganizationsForAction()

        // Обновляем таймер
        updateCountdown()
        checkOverdue()
    }

    function loadOrganizationsForAction() {
        // Запрашиваем ВСЕ организации с файлами
        var orgs = appData.getAllOrganizationsWithReferenceFiles()
        if (orgs) {
            actionDetailsDialog.allOrganizations = orgs
        } else {
            actionDetailsDialog.allOrganizations = []
        }
    }

    function openFilesDialog(orgData, fileType) {
        if (!orgData) return;
        var files = orgData.reference_files || [];
        var filteredFiles = [];
        var title = orgData.name + " - Файлы";

        if (fileType === "all") {
            filteredFiles = files;
            title += " (Все)";
        } else {
            for (var i = 0; i < files.length; i++) {
                if (files[i].file_type === fileType) {
                    filteredFiles.push(files[i]);
                }
            }
            // Красивое название типа для заголовка
            var typeNames = { "word": "Документы", "excel": "Таблицы", "image": "Изображения" };
            title += " (" + (typeNames[fileType] || fileType.toUpperCase()) + ")";
        }

        filesDialogModel.clear();
        for (var j = 0; j < filteredFiles.length; j++) {
            filesDialogModel.append(filteredFiles[j]);
        }

        filesDialogTitle.text = title;

        if (filteredFiles.length > 0) {
            filesDialog.open();
        } else {
            showMessageDialog("Нет файлов", "У организации \"" + orgData.name + "\" нет файлов данного типа.");
        }
    }

    function formatDateTime(dtStr) {
        if (!dtStr) return ""
        var dt = new Date(dtStr)
        if (isNaN(dt.getTime())) return dtStr
        var h = String(dt.getHours()).padStart(2, '0')
        var m = String(dt.getMinutes()).padStart(2, '0')
        var s = String(dt.getSeconds()).padStart(2, '0')
        var day = String(dt.getDate()).padStart(2, '0')
        var month = String(dt.getMonth() + 1).padStart(2, '0')
        var year = dt.getFullYear()
        return day + "." + month + "." + year + " " + h + ":" + m + ":" + s
    }
    
    function getCurrentActionId() {
        if (actionDetailsDialog.executionId <= 0 || actionDetailsDialog.currentActionIndex < 0) return -1
        var actions = appData.getActionExecutionsByExecutionId(actionDetailsDialog.executionId)
        if (actions && actionDetailsDialog.currentActionIndex < actions.length) {
            return actions[actionDetailsDialog.currentActionIndex].id || -1
        }
        return -1
    }
    
    function showMessageDialog(title, message) {
        infoDialogTitle.text = title
        infoDialogText.text = message
        infoDialog.open()
    }

    // Фон
    background: Rectangle {
        id: dialogBackground
        radius: 12
        color: (actionDetailsDialog.isOverdue && actionDetailsDialog.currentStatus !== "completed") ? (overduePulseTimer.running ? "#f5b7b1" : "#ffffff") : "#ffffff"
        border.color: (actionDetailsDialog.isOverdue && actionDetailsDialog.currentStatus !== "completed") ? "#e74c3c" : "#e0e0e0"
        border.width: (actionDetailsDialog.isOverdue && actionDetailsDialog.currentStatus !== "completed") ? 2 : 1
        Behavior on color { ColorAnimation { duration: 400 } }
    }

    // --- Основной макет ---
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0

        // --- Заголовок ---
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            color: "#2c3e50"
            radius: 12
            clip: true

            Label {
                id: actionNameLabel
                anchors.centerIn: parent
                text: "Загрузка..."
                color: "#ffffff"
                font.pointSize: 18
                font.bold: true
            }

            Button {
                anchors.right: parent.right
                anchors.rightMargin: 15
                anchors.verticalCenter: parent.verticalCenter
                text: "✕"
                font.pointSize: 14
                onClicked: actionDetailsDialog.close()
                background: Rectangle { color: "transparent" }
            }
        }

        // --- Разделитель ---
        Rectangle {
            Layout.fillWidth: true
            height: 2
            color: "#34495e"
        }

        // --- Основной контент (2 колонки 50/50) ---
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20

            // === ЛЕВАЯ ЧАСТЬ ===
            ColumnLayout {
                Layout.preferredWidth: parent.width * 0.5
                Layout.fillHeight: true

                // --- Времена (новый дизайн с карточками) ---
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    // Верхний ряд: Время начала и Время окончания (50/50)
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        // Карточка: Время начала
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6

                            Label {
                                text: "Время начала"
                                font.pixelSize: 12
                                color: "#666"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 70
                                radius: 10
                                color: "#ebf5fb"
                                border.color: "#3498db"
                                border.width: 2

                                ColumnLayout {
                                    anchors.centerIn: parent
                                    spacing: 4

                                    // Дата
                                    Text {
                                        id: startDateText
                                        text: {
                                            var dtStr = calculatedStartTimeLabel.text
                                            if (dtStr && dtStr !== "—") {
                                                var parts = dtStr.match(/(\d{2})\.(\d{2})\.(\d{4})/)
                                                if (parts) return parts[1] + "." + parts[2] + "." + parts[3]
                                            }
                                            return "—"
                                        }
                                        font.pixelSize: 14
                                        font.bold: true
                                        color: "#2980b9"
                                        horizontalAlignment: Text.AlignHCenter
                                        Layout.fillWidth: true
                                    }

                                    // Время
                                    Text {
                                        id: startTimeText
                                        text: {
                                            var dtStr = calculatedStartTimeLabel.text
                                            if (dtStr && dtStr !== "—") {
                                                var parts = dtStr.match(/(\d{2}):(\d{2}):(\d{2})/)
                                                if (parts) return parts[1] + ":" + parts[2] + ":" + parts[3]
                                            }
                                            return "—"
                                        }
                                        font.pixelSize: 20
                                        font.bold: true
                                        color: "#2c3e50"
                                        horizontalAlignment: Text.AlignHCenter
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                        }

                        // Карточка: Время окончания
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6

                            Label {
                                text: "Время окончания"
                                font.pixelSize: 12
                                color: "#666"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 70
                                radius: 10
                                color: {
                                    if (actionDetailsDialog.isOverdue && actionDetailsDialog.currentStatus !== "completed") {
                                        return "#fadbd8"
                                    }
                                    return "#e8f8f5"
                                }
                                border.color: {
                                    if (actionDetailsDialog.isOverdue && actionDetailsDialog.currentStatus !== "completed") {
                                        return "#e74c3c"
                                    }
                                    return "#1abc9c"
                                }
                                border.width: 2
                                Behavior on color { ColorAnimation { duration: 400 } }
                                Behavior on border.color { ColorAnimation { duration: 400 } }

                                ColumnLayout {
                                    anchors.centerIn: parent
                                    spacing: 4

                                    // Дата
                                    Text {
                                        id: endDateText
                                        text: {
                                            var dtStr = calculatedEndTimeLabel.text
                                            if (dtStr && dtStr !== "—" && dtStr !== "Не задано") {
                                                var parts = dtStr.match(/(\d{2})\.(\d{2})\.(\d{4})/)
                                                if (parts) return parts[1] + "." + parts[2] + "." + parts[3]
                                            }
                                            return "—"
                                        }
                                        font.pixelSize: 14
                                        font.bold: true
                                        color: {
                                            if (actionDetailsDialog.isOverdue && actionDetailsDialog.currentStatus !== "completed") {
                                                return "#c0392b"
                                            }
                                            return "#16a085"
                                        }
                                        horizontalAlignment: Text.AlignHCenter
                                        Layout.fillWidth: true
                                        Behavior on color { ColorAnimation { duration: 400 } }
                                    }

                                    // Время
                                    Text {
                                        id: endTimeText
                                        text: {
                                            var dtStr = calculatedEndTimeLabel.text
                                            if (dtStr && dtStr !== "—" && dtStr !== "Не задано") {
                                                var parts = dtStr.match(/(\d{2}):(\d{2}):(\d{2})/)
                                                if (parts) return parts[1] + ":" + parts[2] + ":" + parts[3]
                                            }
                                            return "—"
                                        }
                                        font.pixelSize: 20
                                        font.bold: true
                                        color: {
                                            if (actionDetailsDialog.isOverdue && actionDetailsDialog.currentStatus !== "completed") {
                                                return "#e74c3c"
                                            }
                                            return "#2c3e50"
                                        }
                                        horizontalAlignment: Text.AlignHCenter
                                        Layout.fillWidth: true
                                        Behavior on color { ColorAnimation { duration: 400 } }
                                    }
                                }
                            }
                        }
                    }

                    // Нижний ряд: Оставшееся время (по центру)
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Label {
                            text: "Оставшееся время"
                            font.pixelSize: 12
                            color: "#666"
                            horizontalAlignment: Text.AlignHCenter
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 70
                            radius: 10
                            color: {
                                var timeText = remainingTimeLabel.text
                                if (timeText === "⏸ Ожидание") {
                                    return "#ebf5fb"
                                } else if (timeText === "00:00:00" || timeText === "—") {
                                    return "#fadbd8"
                                } else if (remainingTimeLabel.color === "#f39c12") {
                                    return "#fef9e7"
                                }
                                return "#e8f8f5"
                            }
                            border.color: {
                                var timeText = remainingTimeLabel.text
                                if (timeText === "⏸ Ожидание") {
                                    return "#3498db"
                                } else if (timeText === "00:00:00" || timeText === "—") {
                                    return "#e74c3c"
                                } else if (remainingTimeLabel.color === "#f39c12") {
                                    return "#f39c12"
                                }
                                return "#27ae60"
                            }
                            border.width: 2
                            Behavior on color { ColorAnimation { duration: 400 } }
                            Behavior on border.color { ColorAnimation { duration: 400 } }

                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: 4

                                // Метка времени
                                Text {
                                    id: countdownTimeText
                                    text: remainingTimeLabel.text
                                    font.pixelSize: 28
                                    font.bold: true
                                    color: remainingTimeLabel.color
                                    horizontalAlignment: Text.AlignHCenter
                                    Layout.fillWidth: true
                                    Behavior on color { ColorAnimation { duration: 400 } }
                                }
                            }
                        }
                    }

                    // Скрытые оригинальные элементы (для совместимости с логикой)
                    Label { id: calculatedStartTimeLabel; visible: false; text: "—" }
                    Label { id: calculatedEndTimeLabel; visible: false; text: "—" }
                    Label { id: remainingTimeLabel; visible: false; text: "—"; color: "#27ae60" }
                }

                // --- Технический текст ---
                Label {
                    text: "Сведения о порядке выполнения:"
                    font.pixelSize: 13
                    color: "#666"
                    Layout.topMargin: 10
                }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80
                    clip: true
                    TextArea {
                        id: technicalTextContent
                        readOnly: true
                        wrapMode: TextArea.Wrap
                        font.pixelSize: 13
                        background: Rectangle {
                            color: (actionDetailsDialog.isOverdue && actionDetailsDialog.currentStatus !== "completed") ? "#f8d7da" : "#f8f9fa"
                            Behavior on color { ColorAnimation { duration: 400 } }
                            radius: 6; border.color: "#dee2e6"; border.width: 1
                        }
                    }
                }

                // --- Статус (теперь кнопка) ---
                Rectangle {
                    id: statusRectangle
                    Layout.fillWidth: true
                    Layout.preferredHeight: 45
                    radius: 8
                    color: "#95a5a6"
                    Behavior on color { ColorAnimation { duration: 300 } }

                    Label {
                        id: statusLabel
                        anchors.centerIn: parent
                        text: "Загрузка..."
                        color: "#ffffff"
                        font.pixelSize: 16
                        font.bold: true
                    }

                    // Делаем статус кликабельным
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        hoverEnabled: true
                        onClicked: {
                            var component = Qt.createComponent("algorithms/StatusChangeDialog.qml")
                            if (component.status === Component.Ready) {
                                var dialog = component.createObject(Overlay.overlay, {
                                    "actionExecutionId": getCurrentActionId(),
                                    "currentStatus": currentStatus
                                })
                                if (dialog) {
                                    dialog.statusChanged.connect(function(actionId, newStatus) {
                                        // Обновляем статус в БД
                                        var success = appData.updateActionExecutionStatus(actionId, newStatus)
                                        if (success) {
                                            console.log("QML: Статус успешно обновлен на", newStatus)
                                            // Перезагружаем данные действия
                                            loadActionData()
                                        } else {
                                            console.error("QML: Ошибка обновления статуса")
                                            showMessageDialog("Ошибка", "Не удалось обновить статус. Проверьте логи.")
                                        }
                                    })
                                    dialog.open()
                                }
                            } else {
                                console.error("QML: Ошибка создания StatusChangeDialog:", component.errorString())
                            }
                        }
                    }
                }

                // --- Отчётные материалы и Кому доложено ---
                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.topMargin: 10
                    spacing: 15

                    // Отчётные материалы (50% ширины)
                    ColumnLayout {
                        Layout.preferredWidth: parent.width * 0.5
                        Layout.fillHeight: true
                        spacing: 5

                        // Кнопка-заголовок Отчетные материалы
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 30
                            radius: 6
                            color: "#e9ecef"
                            border.color: "#ced4da"
                            border.width: 1
                            
                            Text {
                                anchors.centerIn: parent
                                text: "📂 Отчётные материалы"
                                font.pixelSize: 13
                                font.bold: true
                                color: "#495057"
                            }
                            
                            MouseArea {
                                id: mouseReportMaterials
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                hoverEnabled: true
                                onClicked: {
                                    reportMaterialsDialog.open()
                                }
                            }
                        }

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            ListView {
                                id: reportMaterialsList
                                model: reportMaterialsModel
                                delegate: Rectangle {
                                    width: ListView.view.width
                                    height: 28
                                    color: (actionDetailsDialog.isOverdue && actionDetailsDialog.currentStatus !== "completed") ?
                                        (index % 2 ? "#f5b7b1" : "#f8d7da") :
                                        (index % 2 ? "#f9f9f9" : "#ffffff")
                                    Behavior on color { ColorAnimation { duration: 400 } }
                                    Text {
                                        anchors.fill: parent
                                        anchors.margins: 5
                                        text: {
                                            var p = model.path || ""
                                            var parts = p.replace(/\\/g, "/").split("/")
                                            return parts.length > 0 ? parts[parts.length - 1] : p
                                        }
                                        font.pixelSize: 12
                                        elide: Text.ElideMiddle
                                        verticalAlignment: Text.AlignVCenter
                                        color: "#2980b9"
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: Qt.openUrlExternally("file:///" + model.path.replace(/\\/g, "/"))
                                    }
                                }
                                Label {
                                    anchors.centerIn: parent
                                    text: "Нет материалов"
                                    color: "#95a5a6"
                                    font.pixelSize: 12
                                    font.italic: true
                                    visible: reportMaterialsModel.count === 0
                                }
                            }
                        }
                    }

                    // Кому доложено (50% ширины)
                    ColumnLayout {
                        Layout.preferredWidth: parent.width * 0.5
                        Layout.fillHeight: true
                        spacing: 5

                        // Кнопка-заголовок Кому доложено
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 30
                            radius: 6
                            color: "#e9ecef"
                            border.color: "#ced4da"
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                text: "📢 Кому доложено"
                                font.pixelSize: 13
                                font.bold: true
                                color: "#495057"
                            }

                            MouseArea {
                                id: mouseReportedTo
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                hoverEnabled: true
                                onClicked: {
                                    reportedToDialog.open()
                                }
                            }
                        }

                        // Поле текста "Кому доложено"
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 4
                            color: "#ffffff"
                            border.color: "#dee2e6"
                            border.width: 1

                            TextArea {
                                id: reportedToArea
                                anchors.fill: parent
                                anchors.margins: 5
                                readOnly: true
                                wrapMode: TextArea.Wrap
                                font.pixelSize: 14
                                text: reportedToHidden.text
                                background: Rectangle { color: "transparent" }
                            }
                        }
                    }
                }
                
                // Скрытый элемент для хранения данных "Кому доложено" (для совместимости с логикой обновления)
                Label { id: reportedToHidden; visible: false; text: "—" }

                // --- Кнопки навигации ---
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 15
                    Layout.topMargin: 10

                    // Назад
                    Rectangle {
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 36
                        radius: 8
                        color: {
                            if (prevBtn.pressed) return "#5d6d7e"
                            if (prevBtn.hovered) return "#85929e"
                            return "#95a5a6"
                        }
                        Behavior on color { ColorAnimation { duration: 150 } }
                        enabled: actionDetailsDialog.currentActionIndex > 0
                        opacity: enabled ? 1.0 : 0.5
                        MouseArea {
                            id: prevBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            enabled: parent.enabled
                            onClicked: actionDetailsDialog.switchToPrevious()
                        }
                        Text {
                            anchors.centerIn: parent
                            text: "← Предыдущее"
                            color: "#ffffff"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }

                    Item { Layout.fillWidth: true }

                    // Номер действия
                    Label {
                        text: (actionDetailsDialog.currentActionIndex + 1) + " / " + actionDetailsDialog.totalActions
                        font.pixelSize: 14
                        color: "#2c3e50"
                    }

                    Item { Layout.fillWidth: true }

                    // Вперёд
                    Rectangle {
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 36
                        radius: 8
                        color: {
                            if (nextBtn.pressed) return "#1a6e8e"
                            if (nextBtn.hovered) return "#2980b9"
                            return "#3498db"
                        }
                        Behavior on color { ColorAnimation { duration: 150 } }
                        enabled: actionDetailsDialog.currentActionIndex < actionDetailsDialog.totalActions - 1
                        opacity: enabled ? 1.0 : 0.5
                        MouseArea {
                            id: nextBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            enabled: parent.enabled
                            onClicked: actionDetailsDialog.switchToNext()
                        }
                        Text {
                            anchors.centerIn: parent
                            text: "Следующее →"
                            color: "#ffffff"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }
                }

                // --- Автопереключение ---
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 8
                    spacing: 10

                    // Современный переключатель (toggle switch)
                    Rectangle {
                        width: 44
                        height: 24
                        radius: 12
                        color: actionDetailsDialog.autoSwitch ? "#27ae60" : "#bdc3c7"
                        Behavior on color { ColorAnimation { duration: 200 } }

                        Rectangle {
                            width: 20
                            height: 20
                            radius: 10
                            color: "#ffffff"
                            anchors.verticalCenter: parent.verticalCenter
                            x: actionDetailsDialog.autoSwitch ? parent.width - 22 : 2
                            Behavior on x { NumberAnimation { duration: 200 } }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: actionDetailsDialog.autoSwitch = !actionDetailsDialog.autoSwitch
                        }
                    }

                    Label {
                        text: "Автопереключение при истечении времени"
                        font.pixelSize: 12
                        color: "#666"
                    }
                }
            }

            // === РАЗДЕЛИТЕЛЬ ===
            Rectangle {
                Layout.preferredWidth: 2
                Layout.fillHeight: true
                color: "#dee2e6"
            }

            // === ПРАВАЯ ЧАСТЬ ===
            ColumnLayout {
                Layout.preferredWidth: parent.width * 0.5
                Layout.fillHeight: true

                Label {
                    text: "📚 Справочный материал"
                    font.pointSize: 16
                    font.bold: true
                    Layout.bottomMargin: 10
                }

                // Список организаций
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    ListView {
                        id: orgsList
                        model: actionDetailsDialog.allOrganizations
                        delegate: Rectangle {
                            id: orgDelegate
                            width: ListView.view.width
                            height: 42
                            color: (actionDetailsDialog.isOverdue && actionDetailsDialog.currentStatus !== "completed") ?
                                (index % 2 ? "#f5b7b1" : "#f8d7da") :
                                (index % 2 ? "#f9f9f9" : "#ffffff")
                            Behavior on color { ColorAnimation { duration: 400 } }
                            border.color: "#eee"
                            border.width: 1

                            property string orgNameValue: modelData ? (modelData.name || "Без названия") : ""

                            // MouseArea на весь делегат
                            MouseArea {
                                id: delegateMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    console.log("QML: Клик по организации:", orgDelegate.orgNameValue);
                                    orgNameDialogLabel.text = orgDelegate.orgNameValue;
                                    orgNameDialog.open();
                                }
                            }

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 6
                                spacing: 5

                                // Название организации (клик для просмотра полного имени)
                                Item {
                                    id: orgNameItem
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true

                                    Text {
                                        id: orgName
                                        anchors.fill: parent
                                        anchors.leftMargin: 2
                                        text: modelData ? modelData.name : ""
                                        font.pixelSize: 13
                                        font.bold: true
                                        elide: Text.ElideRight
                                        verticalAlignment: Text.AlignVCenter
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            console.log("QML: Клик по названию организации:", orgName.text);
                                            orgNameDialogLabel.text = orgName.text;
                                            orgNameDialog.open();
                                        }
                                    }
                                }

                                // Телефон
                                Text {
                                    Layout.preferredWidth: 80
                                    text: modelData.phone || "—"
                                    font.pixelSize: 12
                                    color: "#666"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight
                                }

                                // Кнопки файлов
                                RowLayout {
                                    spacing: 4

                                    // Кнопка Документы (Word, ODT, RTF)
                                    Rectangle {
                                        width: 28
                                        height: 28
                                        radius: 6
                                        color: {
                                            if (btnDoc.pressed) return "#1a5276"
                                            if (btnDoc.hovered) return "#2980b9"
                                            return "#3498db"
                                        }
                                        Behavior on color { ColorAnimation { duration: 150 } }
                                        ToolTip.visible: btnDoc.hovered
                                        ToolTip.text: "Документы (TXT, DOC, DOCX, ODT, RTF, PDF, PAGES)"
                                        ToolTip.delay: 300
                                        MouseArea {
                                            id: btnDoc
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: openFilesDialog(modelData, "word")
                                        }
                                        Text {
                                            anchors.centerIn: parent
                                            text: "📄"
                                            font.pixelSize: 14
                                        }
                                    }

                                    // Кнопка Таблицы (Excel и аналоги)
                                    Rectangle {
                                        width: 28
                                        height: 28
                                        radius: 6
                                        color: {
                                            if (btnXls.pressed) return "#1e8449"
                                            if (btnXls.hovered) return "#27ae60"
                                            return "#2ecc71"
                                        }
                                        Behavior on color { ColorAnimation { duration: 150 } }
                                        ToolTip.visible: btnXls.hovered
                                        ToolTip.text: "Таблицы (XLS, XLSX, ODS, CSV, NUMBERS)"
                                        ToolTip.delay: 300
                                        MouseArea {
                                            id: btnXls
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: openFilesDialog(modelData, "excel")
                                        }
                                        Text {
                                            anchors.centerIn: parent
                                            text: "📊"
                                            font.pixelSize: 14
                                        }
                                    }

                                    // Кнопка Изображения
                                    Rectangle {
                                        width: 28
                                        height: 28
                                        radius: 6
                                        color: {
                                            if (btnPdf.pressed) return "#922b21"
                                            if (btnPdf.hovered) return "#cb4335"
                                            return "#e74c3c"
                                        }
                                        Behavior on color { ColorAnimation { duration: 150 } }
                                        ToolTip.visible: btnPdf.hovered
                                        ToolTip.text: "Изображения (JPEG, PNG, GIF, BMP, TIFF, WEBP, SVG, RAW)"
                                        ToolTip.delay: 300
                                        MouseArea {
                                            id: btnPdf
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: openFilesDialog(modelData, "image")
                                        }
                                        Text {
                                            anchors.centerIn: parent
                                            text: "🖼️"
                                            font.pixelSize: 14
                                        }
                                    }

                                    // Кнопка Все файлы
                                    Rectangle {
                                        width: 28
                                        height: 28
                                        radius: 6
                                        color: {
                                            if (btnAll.pressed) return "#7d6608"
                                            if (btnAll.hovered) return "#b7950b"
                                            return "#f1c40f"
                                        }
                                        Behavior on color { ColorAnimation { duration: 150 } }
                                        ToolTip.visible: btnAll.hovered
                                        ToolTip.text: "Все файлы"
                                        ToolTip.delay: 300
                                        MouseArea {
                                            id: btnAll
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: openFilesDialog(modelData, "all")
                                        }
                                        Text {
                                            anchors.centerIn: parent
                                            text: "📁"
                                            font.pixelSize: 14
                                        }
                                    }
                                }
                            }
                        }
                        Label {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.verticalCenter: parent.verticalCenter
                            text: "Нет организаций"
                            color: "#95a5a6"
                            font.pixelSize: 13
                            font.italic: true
                            visible: actionDetailsDialog.allOrganizations.length === 0
                        }
                    }
                }
            }
        }
    }

    onOpened: {
        loadActionData()
    }

    // --- Модель и Диалог для просмотра файлов ---
    ListModel {
        id: filesDialogModel
    }
    
    property alias filesDialogTitleText: filesDialogTitle.text

    Dialog {
        id: filesDialog
        modal: true
        width: 600
        height: 400

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            Label {
                id: filesDialogTitle
                text: "Файлы"
                font.bold: true
                font.pixelSize: 16
                Layout.fillWidth: true
            }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#f8f9fa"
                border.color: "#dee2e6"
                border.width: 1
                radius: 4
                
                ListView {
                    id: filesListView
                    anchors.fill: parent
                    anchors.margins: 4
                    model: filesDialogModel
                    clip: true
                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 30
                        color: index % 2 ? "#ffffff" : "#f0f0f0"
                        radius: 3
                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            verticalAlignment: Text.AlignVCenter
                            text: {
                                var p = model.file_path || ""
                                var parts = p.replace(/\\/g, "/").split("/")
                                return parts.length > 0 ? parts[parts.length - 1] : p
                            }
                            font.pixelSize: 13
                            color: "#2980b9"
                            elide: Text.ElideMiddle
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                var fp = model.file_path || ""
                                if (fp) Qt.openUrlExternally("file:///" + fp.replace(/\\/g, "/"))
                            }
                        }
                    }
                }
            }
        }

        footer: Item {
            width: parent.width
            height: Math.max(30, parent.height * 0.06)

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: parent.width * 0.03
                anchors.bottom: parent.bottom
                anchors.bottomMargin: parent.height * 0.03
                spacing: 10

                Item { Layout.fillWidth: true }

                Button {
                    text: "Закрыть"
                    onClicked: filesDialog.close()
                }
            }
        }
    }

    // --- Информационный диалог ---
    Dialog {
        id: infoDialog
        title: "Информация"
        modal: true
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        width: 400
        height: 200
        
        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            
            Label {
                id: infoDialogTitle
                text: "Заголовок"
                font.bold: true
                font.pixelSize: 16
                Layout.fillWidth: true
            }
            
            Label {
                id: infoDialogText
                text: "Сообщение"
                font.pixelSize: 14
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }

        footer: Item {
            width: parent.width
            height: Math.max(30, parent.height * 0.06)

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: parent.width * 0.03
                anchors.bottom: parent.bottom
                anchors.bottomMargin: parent.height * 0.03
                spacing: 10

                Item { Layout.fillWidth: true }

                Button {
                    text: "Закрыть"
                    onClicked: infoDialog.close()
                }
            }
        }
    }

    // --- Диалог полного названия организации ---
    Dialog {
        id: orgNameDialog
        title: "Название организации"
        modal: true
        width: 500
        height: 150
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2

        Label {
            id: orgNameDialogLabel
            text: ""
            font.pixelSize: 14
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }

        footer: Item {
            width: parent.width
            height: Math.max(30, parent.height * 0.06)

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: parent.width * 0.03
                anchors.bottom: parent.bottom
                anchors.bottomMargin: parent.height * 0.03
                spacing: 10

                Item { Layout.fillWidth: true }

                Button {
                    text: "Закрыть"
                    onClicked: orgNameDialog.close()
                }
            }
        }
    }

    // --- Диалог "Кому доложено" ---
    Dialog {
        id: reportedToDialog
        title: "Кому доложено"
        modal: true
        width: 500
        height: 300
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            Label {
                text: "Введите информацию о докладе:"
                font.pixelSize: 13
                font.bold: true
            }

            TextArea {
                id: reportedToInput
                Layout.fillWidth: true
                Layout.fillHeight: true
                placeholderText: "Например: Командиру в/ч 12345, дежурному по штабу..."
                text: reportedToHidden.text !== "—" ? reportedToHidden.text : ""
                wrapMode: TextArea.Wrap
                font.pixelSize: 13
            }
        }

        footer: Item {
            width: parent.width
            height: Math.max(30, parent.height * 0.06)

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: parent.width * 0.03
                anchors.bottom: parent.bottom
                anchors.bottomMargin: parent.height * 0.03
                spacing: 10

                Item { Layout.fillWidth: true }

                Button {
                    text: "Сохранить"
                    highlighted: true
                    onClicked: reportedToDialog.accept()
                }

                Button {
                    text: "Отмена"
                    onClicked: reportedToDialog.reject()
                }
            }
        }

        onAccepted: {
            var newText = reportedToInput.text.trim();
            if (newText) {
                var actionId = getCurrentActionId();
                if (actionId > 0) {
                    var success = appData.updateActionExecutionReportedTo(actionId, newText);
                    if (success) {
                        reportedToHidden.text = newText;
                        console.log("QML: Поле 'Кому доложено' успешно обновлено.");
                    } else {
                        showMessageDialog("Ошибка", "Не удалось сохранить данные. Проверьте логи.");
                    }
                }
            }
        }

        onRejected: {
            // Восстанавливаем исходный текст
            reportedToInput.text = reportedToHidden.text !== "—" ? reportedToHidden.text : "";
        }
    }

    // --- Диалог "Отчётные материалы" ---
    Dialog {
        id: reportMaterialsDialog
        title: "Отчётные материалы"
        modal: true
        width: 600
        height: 450
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Label {
                    text: "Список материалов:"
                    font.pixelSize: 13
                    font.bold: true
                    Layout.fillWidth: true
                }

                // Кнопка добавить
                Rectangle {
                    width: 80
                    height: 28
                    radius: 6
                    color: {
                        if (addMatBtn.pressed) return "#1e8449"
                        if (addMatBtn.hovered) return "#27ae60"
                        return "#2ecc71"
                    }
                    Behavior on color { ColorAnimation { duration: 150 } }
                    MouseArea {
                        id: addMatBtn
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: reportMatFileDialog.open()
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "➕ Добавить"
                        color: "#ffffff"
                        font.pixelSize: 11
                        font.bold: true
                    }
                }
            }

            // Список материалов
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                ListView {
                    id: reportMaterialsDialogList
                    model: reportMaterialsModel
                    spacing: 4

                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 32
                        radius: 4
                        color: index % 2 ? "#f0f0f0" : "#ffffff"
                        border.color: "#e0e0e0"
                        border.width: 1

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 8

                            Text {
                                Layout.fillWidth: true
                                text: {
                                    var p = model.path || ""
                                    var parts = p.replace(/\\/g, "/").split("/")
                                    return parts.length > 0 ? parts[parts.length - 1] : p
                                }
                                font.pixelSize: 12
                                elide: Text.ElideMiddle
                                verticalAlignment: Text.AlignVCenter
                                color: "#2980b9"

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: Qt.openUrlExternally("file:///" + model.path.replace(/\\/g, "/"))
                                }
                            }

                            // Кнопка удалить
                            Rectangle {
                                width: 24
                                height: 24
                                radius: 4
                                color: {
                                    if (delMatBtn.pressed) return "#922b21"
                                    if (delMatBtn.hovered) return "#cb4335"
                                    return "#e74c3c"
                                }
                                Behavior on color { ColorAnimation { duration: 150 } }
                                MouseArea {
                                    id: delMatBtn
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        var matIndex = index;
                                        var actionId = getCurrentActionId();
                                        if (actionId > 0) {
                                            var success = appData.deleteActionExecutionReportMaterial(actionId, matIndex);
                                            if (success) {
                                                // Перезагружаем материалы
                                                loadActionData();
                                            }
                                        }
                                    }
                                }
                                Text {
                                    anchors.centerIn: parent
                                    text: "✕"
                                    color: "#ffffff"
                                    font.pixelSize: 12
                                    font.bold: true
                                }
                            }
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        text: "Нет материалов"
                        color: "#95a5a6"
                        font.pixelSize: 13
                        font.italic: true
                        visible: reportMaterialsModel.count === 0
                    }
                }
            }
        }

        footer: Item {
            width: parent.width
            height: Math.max(30, parent.height * 0.06)

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: parent.width * 0.03
                anchors.bottom: parent.bottom
                anchors.bottomMargin: parent.height * 0.03
                spacing: 10

                Item { Layout.fillWidth: true }

                Button {
                    text: "Закрыть"
                    onClicked: reportMaterialsDialog.close()
                }
            }
        }
    }

    // --- FileDialog для выбора файла отчётного материала ---
    FileDialog {
        id: reportMatFileDialog
        title: "Выберите файл отчётного материала"
        fileMode: FileDialog.OpenFile
        onAccepted: {
            var selectedFile = reportMatFileDialog.selectedFile;
            if (selectedFile) {
                var localPath = selectedFile.toString().replace(/^file:[\/\\]{2,3}/, "");
                console.log("QML: Выбран файл отчётного материала:", localPath);
                var actionId = getCurrentActionId();
                if (actionId > 0) {
                    var success = appData.addActionExecutionReportMaterial(actionId, localPath);
                    if (success) {
                        console.log("QML: Файл успешно добавлен.");
                        // Перезагружаем данные действия
                        loadActionData();
                    } else {
                        showMessageDialog("Ошибка", "Не удалось добавить файл. Проверьте логи.");
                    }
                }
            }
        }
    }
}
