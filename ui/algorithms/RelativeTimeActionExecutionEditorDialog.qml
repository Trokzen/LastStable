// ui/algorithms/RelativeTimeActionExecutionEditorDialog.qml
// Диалог для редактирования/добавления action_execution с относительным временем
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5
import QtQuick.Dialogs 6.5

Popup {
    id: relativeTimeActionExecutionEditorDialog
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    width: Math.min(parent.width * 0.8, 800)
    height: Math.min(parent.height * 0.85, 600)
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // --- Свойства ---
    property bool isEditMode: false // true - редактирование, false - добавление
    property int executionId: -1 // ID execution'а, к которому принадлежит или будет принадлежать action_execution
    property int currentActionExecutionId: -1 // ID редактируемого action_execution (только в режиме редактирования)

    // --- Сигналы ---
    signal actionExecutionSaved() // Сигнал для уведомления об успешном сохранении/добавлении

    background: Rectangle {
        color: "white"
        border.color: "lightgray"
        radius: 5
    }

    // --- Основной столбец для элементов диалога ---
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        Label {
            id: dialogTitleLabel
            text: relativeTimeActionExecutionEditorDialog.isEditMode ? "Редактировать действие (относительное время)" : "Добавить новое действие (относительное время)"
            font.pointSize: 14
            font.bold: true
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            GridLayout {
                id: formGridLayout
                columns: 2
                columnSpacing: 10
                rowSpacing: 15
                width: parent.width

                Label {
                    text: "Описание:*"
                    Layout.alignment: Qt.AlignRight | Qt.AlignTop // Выравнивание сверху
                }
                TextArea {
                    id: descriptionArea
                    Layout.fillWidth: true
                    Layout.fillHeight: true // Заполняет доступную высоту
                    placeholderText: "Введите описание действия..."
                    wrapMode: TextArea.Wrap
                }

                // --- Ввод относительного времени начала ---
                Label {
                    text: "Начало (дни, часы, минуты, секунды):*"
                    Layout.alignment: Qt.AlignRight
                    font.pixelSize: 11
                    MouseArea {
                        id: startTimeTipMA
                        anchors.fill: parent
                        hoverEnabled: true
                    }
                    ToolTip {
                        text: "Время начала действия относительно времени запуска алгоритма (дни:часы:минуты:секунды)"
                        visible: startTimeTipMA.containsMouse
                        delay: 500
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 5
                    // Поле и кнопки для дней
                    ColumnLayout {
                        spacing: 1
                        TextField {
                            id: startDaysField
                            Layout.preferredWidth: 40
                            placeholderText: "ДД"
                            font.pixelSize: 11
                            text: "00"
                            validator: IntValidator { bottom: 0; top: 99 }
                            selectByMouse: true
                            horizontalAlignment: TextInput.AlignHCenter
                        }
                        RowLayout {
                            spacing: 1
                            Button {
                                text: "▲"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(startDaysField, 1, 0, 99);
                            }
                            Button {
                                text: "▼"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(startDaysField, -1, 0, 99);
                            }
                        }
                    }
                    Text { text: "д"; font.pixelSize: 10 }
                    
                    Text { text: ":"; font.pixelSize: 11 }
                    
                    // Поле и кнопки для часов
                    ColumnLayout {
                        spacing: 1
                        TextField {
                            id: startHoursField
                            Layout.preferredWidth: 40
                            placeholderText: "ЧЧ"
                            font.pixelSize: 11
                            text: "00"
                            validator: IntValidator { bottom: 0; top: 23 }
                            selectByMouse: true
                            horizontalAlignment: TextInput.AlignHCenter
                        }
                        RowLayout {
                            spacing: 1
                            Button {
                                text: "▲"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(startHoursField, 1, 0, 23);
                            }
                            Button {
                                text: "▼"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(startHoursField, -1, 0, 23);
                            }
                        }
                    }
                    Text { text: "ч"; font.pixelSize: 10 }
                    
                    Text { text: ":"; font.pixelSize: 11 }
                    
                    // Поле и кнопки для минут
                    ColumnLayout {
                        spacing: 1
                        TextField {
                            id: startMinutesField
                            Layout.preferredWidth: 40
                            placeholderText: "ММ"
                            font.pixelSize: 11
                            text: "00"
                            validator: IntValidator { bottom: 0; top: 59 }
                            selectByMouse: true
                            horizontalAlignment: TextInput.AlignHCenter
                        }
                        RowLayout {
                            spacing: 1
                            Button {
                                text: "▲"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(startMinutesField, 1, 0, 59);
                            }
                            Button {
                                text: "▼"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(startMinutesField, -1, 0, 59);
                            }
                        }
                    }
                    Text { text: "м"; font.pixelSize: 10 }
                    
                    Text { text: ":"; font.pixelSize: 11 }
                    
                    // Поле и кнопки для секунд
                    ColumnLayout {
                        spacing: 1
                        TextField {
                            id: startSecondsField
                            Layout.preferredWidth: 40
                            placeholderText: "СС"
                            font.pixelSize: 11
                            text: "00"
                            validator: IntValidator { bottom: 0; top: 59 }
                            selectByMouse: true
                            horizontalAlignment: TextInput.AlignHCenter
                        }
                        RowLayout {
                            spacing: 1
                            Button {
                                text: "▲"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(startSecondsField, 1, 0, 59);
                            }
                            Button {
                                text: "▼"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(startSecondsField, -1, 0, 59);
                            }
                        }
                    }
                    Text { text: "с"; font.pixelSize: 10 }
                }

                // --- Ввод относительного времени окончания ---
                Label {
                    text: "Окончание (дни, часы, минуты, секунды):*"
                    Layout.alignment: Qt.AlignRight
                    font.pixelSize: 11
                    MouseArea {
                        id: endTimeTipMA
                        anchors.fill: parent
                        hoverEnabled: true
                    }
                    ToolTip {
                        text: "Время окончания действия относительно времени запуска алгоритма (дни:часы:минуты:секунды)"
                        visible: endTimeTipMA.containsMouse
                        delay: 500
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 5
                    // Поле и кнопки для дней
                    ColumnLayout {
                        spacing: 1
                        TextField {
                            id: endDaysField
                            Layout.preferredWidth: 40
                            placeholderText: "ДД"
                            font.pixelSize: 11
                            text: "00"
                            validator: IntValidator { bottom: 0; top: 99 }
                            selectByMouse: true
                            horizontalAlignment: TextInput.AlignHCenter
                        }
                        RowLayout {
                            spacing: 1
                            Button {
                                text: "▲"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(endDaysField, 1, 0, 99);
                            }
                            Button {
                                text: "▼"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(endDaysField, -1, 0, 99);
                            }
                        }
                    }
                    Text { text: "д"; font.pixelSize: 10 }
                    
                    Text { text: ":"; font.pixelSize: 11 }
                    
                    // Поле и кнопки для часов
                    ColumnLayout {
                        spacing: 1
                        TextField {
                            id: endHoursField
                            Layout.preferredWidth: 40
                            placeholderText: "ЧЧ"
                            font.pixelSize: 11
                            text: "00"
                            validator: IntValidator { bottom: 0; top: 23 }
                            selectByMouse: true
                            horizontalAlignment: TextInput.AlignHCenter
                        }
                        RowLayout {
                            spacing: 1
                            Button {
                                text: "▲"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(endHoursField, 1, 0, 23);
                            }
                            Button {
                                text: "▼"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(endHoursField, -1, 0, 23);
                            }
                        }
                    }
                    Text { text: "ч"; font.pixelSize: 10 }
                    
                    Text { text: ":"; font.pixelSize: 11 }
                    
                    // Поле и кнопки для минут
                    ColumnLayout {
                        spacing: 1
                        TextField {
                            id: endMinutesField
                            Layout.preferredWidth: 40
                            placeholderText: "ММ"
                            font.pixelSize: 11
                            text: "00"
                            validator: IntValidator { bottom: 0; top: 59 }
                            selectByMouse: true
                            horizontalAlignment: TextInput.AlignHCenter
                        }
                        RowLayout {
                            spacing: 1
                            Button {
                                text: "▲"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(endMinutesField, 1, 0, 59);
                            }
                            Button {
                                text: "▼"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(endMinutesField, -1, 0, 59);
                            }
                        }
                    }
                    Text { text: "м"; font.pixelSize: 10 }
                    
                    Text { text: ":"; font.pixelSize: 11 }
                    
                    // Поле и кнопки для секунд
                    ColumnLayout {
                        spacing: 1
                        TextField {
                            id: endSecondsField
                            Layout.preferredWidth: 40
                            placeholderText: "СС"
                            font.pixelSize: 11
                            text: "00"
                            validator: IntValidator { bottom: 0; top: 59 }
                            selectByMouse: true
                            horizontalAlignment: TextInput.AlignHCenter
                        }
                        RowLayout {
                            spacing: 1
                            Button {
                                text: "▲"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(endSecondsField, 1, 0, 59);
                            }
                            Button {
                                text: "▼"
                                font.pixelSize: 6
                                Layout.preferredWidth: 12
                                Layout.preferredHeight: 10
                                onClicked: incrementTimeComponent(endSecondsField, -1, 0, 59);
                            }
                        }
                    }
                    Text { text: "с"; font.pixelSize: 10 }
                }

                // Контактные телефоны
                Label {
                    text: "Телефоны:"
                    Layout.alignment: Qt.AlignRight
                }
                TextField {
                    id: contactPhonesField
                    Layout.fillWidth: true
                    placeholderText: "Введите контактные телефоны..."
                }

                // --- НОВОЕ: FileDialog для отчетных материалов ---
                FileDialog {
                    id: reportMaterialsFileDialog
                    title: "Выберите файлы отчетных материалов"
                    fileMode: FileDialog.OpenFiles // Разрешаем выбор нескольких файлов
                    onAccepted: {
                        console.log("QML RelativeTimeActionExecutionEditorDialog: FileDialog отчетных материалов: Приняты файлы:", reportMaterialsFileDialog.selectedFiles);
                        var selectedFileUrls = reportMaterialsFileDialog.selectedFiles; // Возвращает массив url в формате file:///
                        if (selectedFileUrls && selectedFileUrls.length > 0) {
                            var pathsToAdd = [];
                            for (var i = 0; i < selectedFileUrls.length; i++) {
                                var fileUrl = selectedFileUrls[i];
                                if (fileUrl) {
                                    // Преобразуем URL в локальный путь (удаляем file:///)
                                    var localPath = fileUrl.toString().replace(/^file:[\/\\]{2,3}/, ""); // Убирает file:/// или file:\\
                                    console.log("QML RelativeTimeActionExecutionDialog: FileDialog отчетных материалов: Локальный путь:", localPath);
                                    pathsToAdd.push(localPath);
                                }
                            }
                            if (pathsToAdd.length > 0) {
                                // Добавляем пути в TextArea, разделяя новой строкой
                                var newText = pathsToAdd.join("\n");
                                if (reportMaterialsArea.text.trim() !== "") {
                                    reportMaterialsArea.text += "\n" + newText;
                                } else {
                                    reportMaterialsArea.text = newText;
                                }
                            }
                        }
                    }
                    onRejected: {
                        console.log("QML RelativeTimeActionExecutionDialog: FileDialog отчетных материалов: Отменен пользователем.");
                    }
                }
                // --- ---

                Label {
                    text: "Отчётные материалы:"
                    Layout.alignment: Qt.AlignRight
                }
                // Обернем TextArea и кнопку в ColumnLayout для правильного размещения
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80 // Задаем фиксированную высоту для всей секции
                    spacing: 5

                    TextArea {
                        id: reportMaterialsArea
                        Layout.fillWidth: true
                        Layout.fillHeight: true // Заполняет доступную высоту внутри ColumnLayout
                        placeholderText: "Введите пути к отчётным материалам (по одному на строку)..."
                        wrapMode: TextArea.Wrap
                        selectByMouse: true
                        // - Делаем границу видимой -
                        background: Rectangle {
                            border.color: reportMaterialsArea.activeFocus ? "#3498db" : "#ccc"
                            border.width: 1
                            radius: 2
                            color: "white"
                        }
                        // - -
                    }
                    Button {
                        text: "Добавить файл..."
                        Layout.alignment: Qt.AlignRight
                        onClicked: {
                            console.log("QML RelativeTimeActionExecutionDialog: Нажата кнопка 'Добавить файл...' для отчетных материалов");
                            reportMaterialsFileDialog.open();
                        }
                    }
                }
                // --- ---

                Label {
                    text: "Технический текст:"
                    Layout.alignment: Qt.AlignRight | Qt.AlignTop
                }
                TextArea {
                    id: technicalTextArea
                    Layout.fillWidth: true
                    Layout.preferredHeight: 60
                    placeholderText: "Введите технический текст..."
                    wrapMode: TextArea.Wrap
                    selectByMouse: true
                    background: Rectangle {
                        border.color: technicalTextArea.activeFocus ? "#3498db" : "#ccc"
                        border.width: 1
                        radius: 2
                        color: "white"
                    }
                }

                Label {
                    text: "Кому доложено:"
                    Layout.alignment: Qt.AlignRight
                }
                TextField {
                    id: reportedToField
                    Layout.fillWidth: true
                    placeholderText: "Введите, кому было доложено о выполнении..."
                }

                Label {
                    text: "Примечания:"
                    Layout.alignment: Qt.AlignRight | Qt.AlignTop // Выравнивание сверху
                }
                TextArea {
                    id: notesArea
                    Layout.fillWidth: true
                    Layout.preferredHeight: 60 // Фиксированная высота для текста
                    placeholderText: "Введите дополнительные примечания..."
                    wrapMode: TextArea.Wrap
                }
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
                Layout.fillWidth: true // Заполнитель слева
            }
            Button {
                text: "Отмена"
                onClicked: {
                    console.log("QML RelativeTimeActionExecutionDialog: Нажата кнопка Отмена");
                    relativeTimeActionExecutionEditorDialog.close();
                }
            }
            Button {
                text: "Сохранить"
                onClicked: {
                    console.log("QML RelativeTimeActionExecutionDialog: Нажата кнопка Сохранить");
                    errorMessageLabel.text = "";

                    // --- ВАЛИДАЦИЯ ОПИСАНИЯ ---
                    if (!descriptionArea.text.trim()) {
                        errorMessageLabel.text = "Пожалуйста, заполните описание действия.";
                        return;
                    }

                    // --- ПРОВЕРКА, ЧТО время окончания больше времени начала ---
                    // Преобразуем значения в общее количество секунд для сравнения
                    var startTotalSeconds = 
                        parseInt(startDaysField.text || "0") * 24 * 3600 +
                        parseInt(startHoursField.text || "0") * 3600 +
                        parseInt(startMinutesField.text || "0") * 60 +
                        parseInt(startSecondsField.text || "0");

                    var endTotalSeconds = 
                        parseInt(endDaysField.text || "0") * 24 * 3600 +
                        parseInt(endHoursField.text || "0") * 3600 +
                        parseInt(endMinutesField.text || "0") * 60 +
                        parseInt(endSecondsField.text || "0");

                    if (endTotalSeconds < startTotalSeconds) {
                        errorMessageLabel.text = "Время окончания не может быть меньше времени начала.";
                        return;
                    }

                    // --- СОБИРАЕМ ДАННЫЕ ДЛЯ PYTHON ---
                    var actionExecutionData = {
                        "snapshot_description": descriptionArea.text.trim(),
                        "snapshot_technical_text": technicalTextArea.text.trim(),
                        "relative_start_days": parseInt(startDaysField.text || "0"),
                        "relative_start_hours": parseInt(startHoursField.text || "0"),
                        "relative_start_minutes": parseInt(startMinutesField.text || "0"),
                        "relative_start_seconds": parseInt(startSecondsField.text || "0"),
                        "relative_end_days": parseInt(endDaysField.text || "0"),
                        "relative_end_hours": parseInt(endHoursField.text || "0"),
                        "relative_end_minutes": parseInt(endMinutesField.text || "0"),
                        "relative_end_seconds": parseInt(endSecondsField.text || "0"),
                        "snapshot_contact_phones": contactPhonesField.text,
                        "snapshot_report_materials": reportMaterialsArea.text,
                        "reported_to": reportedToField.text,
                        "notes": notesArea.text
                    };

                    // --- ОТПРАВКА В PYTHON ---
                    var result;
                    if (relativeTimeActionExecutionEditorDialog.isEditMode && relativeTimeActionExecutionEditorDialog.currentActionExecutionId > 0) {
                        console.log("QML RelativeTimeActionExecutionDialog: Обновление action_execution ID", currentActionExecutionId, "в Python:", JSON.stringify(actionExecutionData));
                        result = appData.updateRelativeTimeActionExecution(currentActionExecutionId, actionExecutionData);
                    } else if (!relativeTimeActionExecutionEditorDialog.isEditMode && relativeTimeActionExecutionEditorDialog.executionId > 0) {
                        console.log("QML RelativeTimeActionExecutionDialog: Добавление нового action_execution для execution ID", executionId, "в Python:", JSON.stringify(actionExecutionData));
                        result = appData.addRelativeTimeActionExecution(relativeTimeActionExecutionEditorDialog.executionId, actionExecutionData);
                    } else {
                        errorMessageLabel.text = "Ошибка состояния диалога.";
                        console.error("QML RelativeTimeActionExecutionDialog: Недостаточно данных для сохранения.");
                        return;
                    }

                    if (result === true || (typeof result === 'number' && result > 0)) {
                        console.log("QML RelativeTimeActionExecutionDialog: Успешно сохранено.");
                        relativeTimeActionExecutionEditorDialog.actionExecutionSaved();
                        relativeTimeActionExecutionEditorDialog.close();
                    } else {
                        var errorMsg = typeof result === 'string' ? result : "Неизвестная ошибка";
                        errorMessageLabel.text = "Ошибка: " + errorMsg;
                        console.warn("QML RelativeTimeActionExecutionDialog: Ошибка при сохранении:", errorMsg);
                    }
                }
            }
        }
    }

    // --- Функции для загрузки/сброса данных ---
    /**
     * Сбрасывает диалог для добавления нового action_execution
     */
    function resetForAdd() {
        console.log("QML RelativeTimeActionExecutionDialog: Сброс для добавления");
        isEditMode = false;
        currentActionExecutionId = -1;
        descriptionArea.text = "";
        contactPhonesField.text = "";
        reportMaterialsArea.text = "";
        technicalTextArea.text = "";
        reportedToField.text = "";
        notesArea.text = "";
        errorMessageLabel.text = "";
        dialogTitleLabel.text = "Добавить новое действие (относительное время)";

        // Установка значений по умолчанию
        startDaysField.text = "00";
        startHoursField.text = "00";
        startMinutesField.text = "00";
        startSecondsField.text = "00";

        endDaysField.text = "00";
        endHoursField.text = "00";
        endMinutesField.text = "00";
        endSecondsField.text = "00";
    }

    /**
    * Загружает данные action_execution для редактирования
    */
    function loadDataForEdit(actionExecutionData) {
        console.log("QML RelativeTimeActionExecutionDialog: Загрузка данных:", JSON.stringify(actionExecutionData));
        if (!actionExecutionData || typeof actionExecutionData !== 'object') {
            errorMessageLabel.text = "Ошибка загрузки данных.";
            return;
        }

        isEditMode = true;
        currentActionExecutionId = actionExecutionData.id || -1;
        descriptionArea.text = actionExecutionData.snapshot_description || "";
        contactPhonesField.text = actionExecutionData.snapshot_contact_phones || "";
        reportMaterialsArea.text = actionExecutionData.snapshot_report_materials || "";
        technicalTextArea.text = actionExecutionData.snapshot_technical_text || "";
        reportedToField.text = actionExecutionData.reported_to || "";
        notesArea.text = actionExecutionData.notes || "";
        errorMessageLabel.text = "";
        dialogTitleLabel.text = "Редактировать действие (относительное время)";

        // Устанавливаем значения относительного времени
        startDaysField.text = String(actionExecutionData.relative_start_days || 0).padStart(2, '0');
        startHoursField.text = String(actionExecutionData.relative_start_hours || 0).padStart(2, '0');
        startMinutesField.text = String(actionExecutionData.relative_start_minutes || 0).padStart(2, '0');
        startSecondsField.text = String(actionExecutionData.relative_start_seconds || 0).padStart(2, '0');

        endDaysField.text = String(actionExecutionData.relative_end_days || 0).padStart(2, '0');
        endHoursField.text = String(actionExecutionData.relative_end_hours || 0).padStart(2, '0');
        endMinutesField.text = String(actionExecutionData.relative_end_minutes || 0).padStart(2, '0');
        endSecondsField.text = String(actionExecutionData.relative_end_seconds || 0).padStart(2, '0');
    }

    function incrementTimeComponent(textField, delta, minVal, maxVal) {
        var text = textField.text || "00";
        var value = parseInt(text, 10) || 0;
        
        value += delta;
        
        // Обеспечиваем цикличность в пределах допустимого диапазона
        if (value < minVal) {
            value = maxVal;
        } else if (value > maxVal) {
            value = minVal;
        }
        
        var newText = value.toString().padStart(2, '0');
        textField.text = newText;
    }

    onOpened: {
        console.log("QML RelativeTimeActionExecutionDialog: Диалог открыт. Режим:", isEditMode ? "Редактирование" : "Добавление");
        errorMessageLabel.text = "";
        // Фокус на первое поле
        if (isEditMode) {
            descriptionArea.forceActiveFocus();
        } else {
            // При добавлении тоже фокус на описание
            descriptionArea.forceActiveFocus();
        }
    }
}