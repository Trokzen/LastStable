// ui/ActionEditorDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5
import QtQuick.Dialogs 6.5 // Для FileDialog

Popup {
    id: actionEditorDialog
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    width: Math.min(parent.width * 0.9, 900) // Увеличено
    height: Math.min(parent.height * 0.9, 700) // Увеличено
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // --- Свойства ---
    property bool isEditMode: false // <-- Добавьте эту строку, если её нет
    property int currentActionId: -1
    property int currentAlgorithmId: -1

    signal actionSaved()

    // --- Для выбора файлов ---
    FileDialog {
        id: fileDialog
        title: "Выберите файл"
        // Выбираем один или несколько файлов
        fileMode: FileDialog.OpenFiles
        onAccepted: {
            console.log("QML ActionEditorDialog: FileDialog accepted. Selected files:", selectedFiles)
            // Обрабатываем выбранные файлы
            if (selectedFiles.length > 0) {
                // Получаем текущий текст из TextArea
                var currentText = reportMaterialsArea.text
                var newText = ""
                // Преобразуем URL в локальный путь (убираем "file:///")
                for (var i = 0; i < selectedFiles.length; i++) {
                    var filePath = selectedFiles[i].toString()
                    if (filePath.startsWith("file:///")) {
                        // Для Windows убираем "file:///", для других ОС может потребоваться другая обработка
                        filePath = filePath.substring(8)
                    }
                    newText += filePath
                    if (i < selectedFiles.length - 1) {
                        newText += "\n" // Разделяем пути новой строкой
                    }
                }

                if (currentText.length > 0 && !currentText.endsWith("\n")) {
                    currentText += "\n"
                }
                reportMaterialsArea.text = currentText + newText
            }
        }
        onRejected: {
            console.log("QML ActionEditorDialog: FileDialog rejected")
        }
    }
    // --- ---

    background: Rectangle {
        color: "white"
        border.color: "lightgray"
        radius: 5
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        Label {
            text: isEditMode ? "Редактировать действие" : "Добавить новое действие"
            font.pointSize: 14
            font.bold: true
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            GridLayout {
                columns: 2
                columnSpacing: 10
                rowSpacing: 15 // Увеличено для лучшей читаемости
                width: parent.width

                // --- ОПИСАНИЕ ---
                Label {
                    text: "Описание:*"
                    Layout.alignment: Qt.AlignRight | Qt.AlignTop
                }
                TextArea {
                    id: descriptionArea
                    Layout.fillWidth: true
                    Layout.minimumHeight: 80 // Увеличена высота
                    placeholderText: "Введите описание действия..."
                    wrapMode: TextArea.Wrap
                    // --- Делаем границу видимой ---
                    background: Rectangle {
                        border.color: descriptionArea.activeFocus ? "#3498db" : "#ccc"
                        border.width: 1
                        radius: 2
                        color: "white"
                    }
                    // --- ---
                }
                // --- ---

                // --- ВРЕМЯ НАЧАЛА ---
                Label {
                    text: "Время начала (смещение):*"
                    Layout.alignment: Qt.AlignRight | Qt.AlignTop
                    ToolTip.text: "Введите смещение времени начала действия"
                    ToolTip.visible: hovered
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5

                    // Поля ввода дней, часов, минут, секунд
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        // Дни
                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 2
                            Label {
                                text: "Дни"
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }
                            TextField {
                                id: startDaysField
                                Layout.preferredWidth: 60
                                Layout.alignment: Qt.AlignHCenter
                                placeholderText: "0"
                                text: "0"
                                validator: IntValidator { bottom: 0 }
                                horizontalAlignment: TextInput.AlignHCenter
                                // --- Делаем границу видимой ---
                                background: Rectangle {
                                    border.color: startDaysField.activeFocus ? "#3498db" : "#ccc"
                                    border.width: 1
                                    radius: 2
                                    color: "white"
                                }
                                // --- ---
                            }
                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 2
                                Button {
                                    text: "▲"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(startDaysField.text) || 0;
                                        startDaysField.text = (currentValue + 1).toString();
                                    }
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(startDaysField.text) || 0;
                                        startDaysField.text = Math.max(0, currentValue - 1).toString();
                                    }
                                }
                            }
                        }

                        // Часы
                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 2
                            Label {
                                text: "Часы"
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }
                            TextField {
                                id: startHoursField
                                Layout.preferredWidth: 60
                                Layout.alignment: Qt.AlignHCenter
                                placeholderText: "00"
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 23 }
                                horizontalAlignment: TextInput.AlignHCenter
                                // --- Делаем границу видимой ---
                                background: Rectangle {
                                    border.color: startHoursField.activeFocus ? "#3498db" : "#ccc"
                                    border.width: 1
                                    radius: 2
                                    color: "white"
                                }
                                // --- ---
                            }
                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 2
                                Button {
                                    text: "▲"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(startHoursField.text) || 0;
                                        var newValue = (currentValue + 1) % 24;
                                        startHoursField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(startHoursField.text) || 0;
                                        var newValue = (currentValue - 1 + 24) % 24;
                                        startHoursField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                            }
                        }

                        // Минуты
                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 2
                            Label {
                                text: "Минуты"
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }
                            TextField {
                                id: startMinutesField
                                Layout.preferredWidth: 60
                                Layout.alignment: Qt.AlignHCenter
                                placeholderText: "00"
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 59 }
                                horizontalAlignment: TextInput.AlignHCenter
                                // --- Делаем границу видимой ---
                                background: Rectangle {
                                    border.color: startMinutesField.activeFocus ? "#3498db" : "#ccc"
                                    border.width: 1
                                    radius: 2
                                    color: "white"
                                }
                                // --- ---
                            }
                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 2
                                Button {
                                    text: "▲"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(startMinutesField.text) || 0;
                                        var newValue = (currentValue + 1) % 60;
                                        startMinutesField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(startMinutesField.text) || 0;
                                        var newValue = (currentValue - 1 + 60) % 60;
                                        startMinutesField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                            }
                        }

                        // Секунды
                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 2
                            Label {
                                text: "Секунды"
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }
                            TextField {
                                id: startSecondsField
                                Layout.preferredWidth: 60
                                Layout.alignment: Qt.AlignHCenter
                                placeholderText: "00"
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 59 }
                                horizontalAlignment: TextInput.AlignHCenter
                                // --- Делаем границу видимой ---
                                background: Rectangle {
                                    border.color: startSecondsField.activeFocus ? "#3498db" : "#ccc"
                                    border.width: 1
                                    radius: 2
                                    color: "white"
                                }
                                // --- ---
                            }
                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 2
                                Button {
                                    text: "▲"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(startSecondsField.text) || 0;
                                        var newValue = (currentValue + 1) % 60;
                                        startSecondsField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(startSecondsField.text) || 0;
                                        var newValue = (currentValue - 1 + 60) % 60;
                                        startSecondsField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                            }
                        }
                    }

                    // Поле для отображения форматированного времени
                    TextField {
                        id: startOffsetPreviewField
                        Layout.fillWidth: true
                        readOnly: true
                        placeholderText: "Формат: dd:hh:mm:ss"
                        text: "0:00:00:00"
                        // --- Делаем границу видимой ---
                        background: Rectangle {
                            border.color: "#ccc"
                            border.width: 1
                            radius: 2
                            color: "#f0f0f0"
                        }
                        // --- ---
                    }
                }
                // --- ---

                // --- ВРЕМЯ ОКОНЧАНИЯ ---
                Label {
                    text: "Время окончания (смещение):*"
                    Layout.alignment: Qt.AlignRight | Qt.AlignTop
                    ToolTip.text: "Введите смещение времени окончания действия"
                    ToolTip.visible: hovered
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5

                    // Поля ввода дней, часов, минут, секунд
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        // Дни
                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 2
                            Label {
                                text: "Дни"
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }
                            TextField {
                                id: endDaysField
                                Layout.preferredWidth: 60
                                Layout.alignment: Qt.AlignHCenter
                                placeholderText: "0"
                                text: "0"
                                validator: IntValidator { bottom: 0 }
                                horizontalAlignment: TextInput.AlignHCenter
                                // --- Делаем границу видимой ---
                                background: Rectangle {
                                    border.color: endDaysField.activeFocus ? "#3498db" : "#ccc"
                                    border.width: 1
                                    radius: 2
                                    color: "white"
                                }
                                // --- ---
                            }
                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 2
                                Button {
                                    text: "▲"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(endDaysField.text) || 0;
                                        endDaysField.text = (currentValue + 1).toString();
                                    }
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(endDaysField.text) || 0;
                                        endDaysField.text = Math.max(0, currentValue - 1).toString();
                                    }
                                }
                            }
                        }

                        // Часы
                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 2
                            Label {
                                text: "Часы"
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }
                            TextField {
                                id: endHoursField
                                Layout.preferredWidth: 60
                                Layout.alignment: Qt.AlignHCenter
                                placeholderText: "00"
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 23 }
                                horizontalAlignment: TextInput.AlignHCenter
                                // --- Делаем границу видимой ---
                                background: Rectangle {
                                    border.color: endHoursField.activeFocus ? "#3498db" : "#ccc"
                                    border.width: 1
                                    radius: 2
                                    color: "white"
                                }
                                // --- ---
                            }
                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 2
                                Button {
                                    text: "▲"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(endHoursField.text) || 0;
                                        var newValue = (currentValue + 1) % 24;
                                        endHoursField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(endHoursField.text) || 0;
                                        var newValue = (currentValue - 1 + 24) % 24;
                                        endHoursField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                            }
                        }

                        // Минуты
                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 2
                            Label {
                                text: "Минуты"
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }
                            TextField {
                                id: endMinutesField
                                Layout.preferredWidth: 60
                                Layout.alignment: Qt.AlignHCenter
                                placeholderText: "00"
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 59 }
                                horizontalAlignment: TextInput.AlignHCenter
                                // --- Делаем границу видимой ---
                                background: Rectangle {
                                    border.color: endMinutesField.activeFocus ? "#3498db" : "#ccc"
                                    border.width: 1
                                    radius: 2
                                    color: "white"
                                }
                                // --- ---
                            }
                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 2
                                Button {
                                    text: "▲"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(endMinutesField.text) || 0;
                                        var newValue = (currentValue + 1) % 60;
                                        endMinutesField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(endMinutesField.text) || 0;
                                        var newValue = (currentValue - 1 + 60) % 60;
                                        endMinutesField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                            }
                        }

                        // Секунды
                        ColumnLayout {
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 2
                            Label {
                                text: "Секунды"
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth: true
                            }
                            TextField {
                                id: endSecondsField
                                Layout.preferredWidth: 60
                                Layout.alignment: Qt.AlignHCenter
                                placeholderText: "00"
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 59 }
                                horizontalAlignment: TextInput.AlignHCenter
                                // --- Делаем границу видимой ---
                                background: Rectangle {
                                    border.color: endSecondsField.activeFocus ? "#3498db" : "#ccc"
                                    border.width: 1
                                    radius: 2
                                    color: "white"
                                }
                                // --- ---
                            }
                            RowLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 2
                                Button {
                                    text: "▲"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(endSecondsField.text) || 0;
                                        var newValue = (currentValue + 1) % 60;
                                        endSecondsField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 8
                                    Layout.preferredWidth: 20
                                    Layout.preferredHeight: 15
                                    onClicked: {
                                        var currentValue = parseInt(endSecondsField.text) || 0;
                                        var newValue = (currentValue - 1 + 60) % 60;
                                        endSecondsField.text = newValue.toString().padStart(2, '0');
                                    }
                                }
                            }
                        }
                    }

                    // Поле для отображения форматированного времени
                    TextField {
                        id: endOffsetPreviewField
                        Layout.fillWidth: true
                        readOnly: true
                        placeholderText: "Формат: dd:hh:mm:ss"
                        text: "0:00:00:00"
                        // --- Делаем границу видимой ---
                        background: Rectangle {
                            border.color: "#ccc"
                            border.width: 1
                            radius: 2
                            color: "#f0f0f0"
                        }
                        // --- ---
                    }
                }

                // --- КОНТАКТНЫЕ ТЕЛЕФОНЫ ---
                Label {
                    text: "Контактные телефоны:"
                    Layout.alignment: Qt.AlignRight | Qt.AlignTop
                }
                TextArea {
                    id: contactPhonesArea
                    Layout.fillWidth: true
                    Layout.minimumHeight: 60
                    placeholderText: "Введите контактные телефоны (через запятую или новую строку)..."
                    wrapMode: TextArea.Wrap
                    // --- Делаем границу видимой ---
                    background: Rectangle {
                        border.color: contactPhonesArea.activeFocus ? "#3498db" : "#ccc"
                        border.width: 1
                        radius: 2
                        color: "white"
                    }
                    // --- ---
                }
                // --- ---

                // --- ОТЧЕТНЫЕ МАТЕРИАЛЫ ---
                Label {
                    text: "Отчетные материалы:"
                    Layout.alignment: Qt.AlignRight | Qt.AlignTop
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 100
                    spacing: 5

                    TextArea {
                        id: reportMaterialsArea
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        placeholderText: "Введите пути/ссылки на отчетные материалы (через новую строку)..."
                        wrapMode: TextArea.Wrap
                        // --- Делаем границу видимой ---
                        background: Rectangle {
                            border.color: reportMaterialsArea.activeFocus ? "#3498db" : "#ccc"
                            border.width: 1
                            radius: 2
                            color: "white"
                        }
                        // --- ---
                    }

                    Button {
                        text: "Добавить файл..."
                        onClicked: {
                            console.log("QML ActionEditorDialog: Нажата кнопка 'Добавить файл'")
                            fileDialog.open()
                        }
                    }
                }
                // --- ---
            }
        }

        // Сообщения об ошибках
        Label {
            id: errorMessageLabel
            Layout.fillWidth: true
            color: "red"
            wrapMode: Text.WordWrap
            visible: text !== ""
        }

        // Кнопки
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Item {
                Layout.fillWidth: true
            }
            Button {
                text: "Отмена"
                onClicked: {
                    console.log("QML ActionEditorDialog: Нажата кнопка Отмена");
                    actionEditorDialog.close();
                }
            }
            Button {
                text: isEditMode ? "Сохранить" : "Добавить"
                onClicked: {
                    console.log("QML ActionEditorDialog: Нажата кнопка Сохранить/Добавить");
                    errorMessageLabel.text = "";

                    // Валидация
                    if (!descriptionArea.text.trim()) {
                        errorMessageLabel.text = "Пожалуйста, заполните описание действия.";
                        return;
                    }

                    // Подготавливаем данные
                    var startOffset = `${startDaysField.text}:${startHoursField.text.padStart(2, '0')}:${startMinutesField.text.padStart(2, '0')}:${startSecondsField.text.padStart(2, '0')}`;
                    var endOffset = `${endDaysField.text}:${endHoursField.text.padStart(2, '0')}:${endMinutesField.text.padStart(2, '0')}:${endSecondsField.text.padStart(2, '0')}`;

                    var actionData = {
                        "algorithm_id": currentAlgorithmId, // Всегда передаем, даже при редактировании
                        "description": descriptionArea.text.trim(),
                        "start_offset": startOffset,
                        "end_offset": endOffset,
                        "contact_phones": contactPhonesArea.text,
                        "report_materials": reportMaterialsArea.text
                    };

                    var result;
                    if (isEditMode) {
                        console.log("QML ActionEditorDialog: Отправляем обновление действия ID", currentActionId, "в Python:", JSON.stringify(actionData));
                        result = appData.updateAction(currentActionId, actionData);
                    } else {
                        console.log("QML ActionEditorDialog: Отправляем новое действие для алгоритма ID", currentAlgorithmId, "в Python:", JSON.stringify(actionData));
                        result = appData.addAction(actionData);
                    }

                    if (result === true || (typeof result === 'number' && result > 0)) {
                        console.log("QML ActionEditorDialog: Действие успешно сохранено/добавлено. Результат:", result);
                        actionEditorDialog.actionSaved();
                        actionEditorDialog.close();
                    } else {
                        var errorMsg = "Неизвестная ошибка";
                        if (typeof result === 'string') {
                            errorMsg = result;
                        } else if (result === false) {
                            errorMsg = "Не удалось выполнить операцию. Проверьте данные.";
                        } else if (result === -1) {
                            errorMsg = "Ошибка при добавлении действия.";
                        }
                        errorMessageLabel.text = "Ошибка: " + errorMsg;
                        console.warn("QML ActionEditorDialog: Ошибка при сохранении/добавлении действия:", errorMsg);
                    }
                }
            }
        }
    }

    /**
     * Сбрасывает диалог для добавления нового действия
     */
    function resetForAdd(algorithmId) {
        console.log("QML ActionEditorDialog: Сброс для добавления нового действия для алгоритма ID:", algorithmId);
        isEditMode = false;
        currentActionId = -1;
        currentAlgorithmId = algorithmId; // Запоминаем ID алгоритма
        descriptionArea.text = "";

        // Сброс времени начала
        startDaysField.text = "0";
        startHoursField.text = "00";
        startMinutesField.text = "00";
        startSecondsField.text = "00";
        updateStartOffsetPreview();

        // Сброс времени окончания
        endDaysField.text = "0";
        endHoursField.text = "00";
        endMinutesField.text = "00";
        endSecondsField.text = "00";
        updateEndOffsetPreview();

        contactPhonesArea.text = "";
        reportMaterialsArea.text = "";
        errorMessageLabel.text = "";
    }

    /**
     * Загружает данные действия для редактирования
     */
    function loadDataForEdit(actionData) {
        console.log("QML ActionEditorDialog: Загрузка данных для редактирования:", JSON.stringify(actionData));
        isEditMode = true;
        currentActionId = actionData.id;
        currentAlgorithmId = actionData.algorithm_id; // Запоминаем ID алгоритма
        descriptionArea.text = actionData.description || "";

        // Загрузка времени начала
        loadStartOffsetFromString(actionData.start_offset || "");

        // Загрузка времени окончания
        loadEndOffsetFromString(actionData.end_offset || "");

        contactPhonesArea.text = actionData.contact_phones || "";
        reportMaterialsArea.text = actionData.report_materials || "";
        errorMessageLabel.text = "";
    }

    function updateStartOffsetPreview() {
        var days = parseInt(startDaysField.text) || 0;
        var hours = parseInt(startHoursField.text) || 0;
        var minutes = parseInt(startMinutesField.text) || 0;
        var seconds = parseInt(startSecondsField.text) || 0;
        startOffsetPreviewField.text = `${days}:${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    /**
    * Обновляет поле предпросмотра времени окончания
    */
    function updateEndOffsetPreview() {
        var days = parseInt(endDaysField.text) || 0;
        var hours = parseInt(endHoursField.text) || 0;
        var minutes = parseInt(endMinutesField.text) || 0;
        var seconds = parseInt(endSecondsField.text) || 0;
        endOffsetPreviewField.text = `${days}:${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    /**
    * Загружает время начала из строки формата dd:hh:mm:ss
    */
    function loadStartOffsetFromString(timeString) {
        console.log("QML ActionEditorDialog: loadStartOffsetFromString called with:", timeString);
        if (!timeString) {
            startDaysField.text = "0";
            startHoursField.text = "00";
            startMinutesField.text = "00";
            startSecondsField.text = "00";
            updateStartOffsetPreview();
            return;
        }

        var parts = timeString.split(":");
        if (parts.length === 4) {
            // Формат dd:hh:mm:ss
            startDaysField.text = parts[0] || "0";
            startHoursField.text = (parts[1] || "00").padStart(2, '0');
            startMinutesField.text = (parts[2] || "00").padStart(2, '0');
            startSecondsField.text = (parts[3] || "00").padStart(2, '0');
        } else if (parts.length === 3) {
            // Формат hh:mm:ss
            startDaysField.text = "0";
            startHoursField.text = (parts[0] || "00").padStart(2, '0');
            startMinutesField.text = (parts[1] || "00").padStart(2, '0');
            startSecondsField.text = (parts[2] || "00").padStart(2, '0');
        } else {
            // Неизвестный формат, устанавливаем значения по умолчанию
            startDaysField.text = "0";
            startHoursField.text = "00";
            startMinutesField.text = "00";
            startSecondsField.text = "00";
        }
        updateStartOffsetPreview();
    }

    /**
    * Загружает время окончания из строки формата dd:hh:mm:ss
    */
    function loadEndOffsetFromString(timeString) {
        console.log("QML ActionEditorDialog: loadEndOffsetFromString called with:", timeString);
        if (!timeString) {
            endDaysField.text = "0";
            endHoursField.text = "00";
            endMinutesField.text = "00";
            endSecondsField.text = "00";
            updateEndOffsetPreview();
            return;
        }

        var parts = timeString.split(":");
        if (parts.length === 4) {
            // Формат dd:hh:mm:ss
            endDaysField.text = parts[0] || "0";
            endHoursField.text = (parts[1] || "00").padStart(2, '0');
            endMinutesField.text = (parts[2] || "00").padStart(2, '0');
            endSecondsField.text = (parts[3] || "00").padStart(2, '0');
        } else if (parts.length === 3) {
            // Формат hh:mm:ss
            endDaysField.text = "0";
            endHoursField.text = (parts[0] || "00").padStart(2, '0');
            endMinutesField.text = (parts[1] || "00").padStart(2, '0');
            endSecondsField.text = (parts[2] || "00").padStart(2, '0');
        } else {
            // Неизвестный формат, устанавливаем значения по умолчанию
            endDaysField.text = "0";
            endHoursField.text = "00";
            endMinutesField.text = "00";
            endSecondsField.text = "00";
        }
        updateEndOffsetPreview();
    }

    // Подключаем обновление предпросмотра при изменении полей
    Connections {
        target: startDaysField
        function onTextChanged() { updateStartOffsetPreview(); }
    }
    Connections {
        target: startHoursField
        function onTextChanged() { updateStartOffsetPreview(); }
    }
    Connections {
        target: startMinutesField
        function onTextChanged() { updateStartOffsetPreview(); }
    }
    Connections {
        target: startSecondsField
        function onTextChanged() { updateStartOffsetPreview(); }
    }

    Connections {
        target: endDaysField
        function onTextChanged() { updateEndOffsetPreview(); }
    }
    Connections {
        target: endHoursField
        function onTextChanged() { updateEndOffsetPreview(); }
    }
    Connections {
        target: endMinutesField
        function onTextChanged() { updateEndOffsetPreview(); }
    }
    Connections {
        target: endSecondsField
        function onTextChanged() { updateEndOffsetPreview(); }
    }

    onOpened: {
        console.log("QML ActionEditorDialog: Диалог открыт.");
        errorMessageLabel.text = "";
        // --- АВТОВЫДЕЛЕНИЕ ОПИСАНИЯ ---
        // Даем фокус и выделяем текст в descriptionArea
        descriptionArea.forceActiveFocus();
        descriptionArea.selectAll();
    }
}