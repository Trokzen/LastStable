// ui/algorithms/ActionExecutionEditorDialog.qml
// Диалог для редактирования/добавления action_execution
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5
import QtQuick.Dialogs 6.5

Popup {
    id: actionExecutionEditorDialog
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    width: Math.min(parent.width * 0.8, 800) // 80% ширины или максимум 600
    height: Math.min(parent.height * 0.85, 600) // Увеличена высота для новых полей
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // --- Свойства ---
    property bool isEditMode: false // true - редактирование, false - добавление
    property int executionId: -1 // ID execution'а, к которому принадлежит или будет принадлежать action_execution
    property int currentActionExecutionId: -1 // ID редактируемого action_execution (только в режиме редактирования)

    // --- Сигналы ---
    signal actionExecutionSaved() // Сигнал для уведомления об успешном сохранении/добавлении

    // --- Вспомогательные свойства для управления динамическими соединениями ---
    property var startTimeCalendarConnection: undefined
    property var endTimeCalendarConnection: undefined

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
            text: actionExecutionEditorDialog.isEditMode ? "Редактировать действие" : "Добавить новое действие"
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

                // --- НОВОЕ: Ввод абсолютного фактического времени начала ---
                Label {
                    text: "Начало:*"
                    Layout.alignment: Qt.AlignRight
                    font.pixelSize: 11 // <-- Уменьшено
                    MouseArea {
                        id: startTimeTipMA_start
                        anchors.fill: parent
                        hoverEnabled: true
                    }
                    ToolTip {
                        text: "Фактическая абсолютная дата и время начала выполнения действия"
                        visible: startTimeTipMA_start.containsMouse
                        delay: 500 // <-- Добавлено для ToolTip
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3 // <-- Уменьшено

                    // --- ПОЛЕ ДЛЯ ДАТЫ ---
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 3 // <-- Уменьшено
                        TextField {
                            id: actualStartDateField
                            Layout.fillWidth: true
                            // Layout.preferredWidth: 80 // <-- Можно задать фиксированную ширину, если нужно
                            placeholderText: "дд.ММ.гггг"
                            font.pixelSize: 11 // <-- Уменьшено
                            text: "" // Будет установлено в resetForAdd/loadDataForEdit
                            selectByMouse: true
                            readOnly: true // Только для чтения, чтобы избежать ручного ввода
                        }
                        Button {
                            id: actualStartDateCalendarButton
                            text: "📅"
                            font.pixelSize: 12 // <-- Уменьшено
                            Layout.preferredWidth: 30 // <-- Уменьшено
                            Layout.preferredHeight: 25 // <-- Уменьшено
                            onClicked: {
                                console.log("QML ActionExecutionEditorDialog: Нажата кнопка календаря для фактической даты начала.");
                                // --- ИНИЦИАЛИЗАЦИЯ КАЛЕНДАРЯ ---
                                var currentDateText = actualStartDateField.text.trim();
                                var dateRegex = /^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[012])\.\d{4}$/;
                                if (dateRegex.test(currentDateText)) {
                                    var parts = currentDateText.split('.');
                                    var day = parseInt(parts[0], 10);
                                    var month = parseInt(parts[1], 10) - 1;
                                    var year = parseInt(parts[2], 10);
                                    var testDate = new Date(year, month, day);
                                    if (testDate.getDate() === day && testDate.getMonth() === month && testDate.getFullYear() === year) {
                                        customCalendarPicker.selectedDate = testDate;
                                        console.log("QML ActionExecutionEditorDialog: CustomCalendarPicker инициализирован датой из поля начала:", testDate);
                                    } else {
                                        customCalendarPicker.selectedDate = new Date();
                                        console.log("QML ActionExecutionEditorDialog: CustomCalendarPicker инициализирован текущей датой (некорректная дата в поле начала).");
                                    }
                                } else {
                                    customCalendarPicker.selectedDate = new Date();
                                    console.log("QML ActionExecutionEditorDialog: CustomCalendarPicker инициализирован текущей датой (некорректный формат в поле начала).");
                                }
                                // --- ---

                                // --- ПОДКЛЮЧАЕМ ОБРАБОТЧИК ---
                                if (typeof startTimeCalendarConnection !== 'undefined' && startTimeCalendarConnection) {
                                    startTimeCalendarConnection.destroy();
                                }
                                startTimeCalendarConnection = Qt.createQmlObject(`
                                    import QtQuick 6.5;
                                    Connections {
                                        target: customCalendarPicker;
                                        function onDateSelected(date) {
                                            console.log("QML ActionExecutionEditorDialog: CustomCalendarPicker (Начало): Дата выбрана:", date);
                                            var year = date.getFullYear();
                                            var month = String(date.getMonth() + 1).padStart(2, '0');
                                            var day = String(date.getDate()).padStart(2, '0');
                                            var formattedDate = day + "." + month + "." + year;
                                            actualStartDateField.text = formattedDate;
                                            console.log("QML ActionExecutionEditorDialog: CustomCalendarPicker (Начало): Установлена новая дата в поле начала:", formattedDate);
                                            if (typeof startTimeCalendarConnection !== 'undefined' && startTimeCalendarConnection) {
                                                startTimeCalendarConnection.destroy();
                                                startTimeCalendarConnection = undefined;
                                            }
                                        }
                                    }
                                `, actionExecutionEditorDialog, "startTimeCalendarConnectionDynamic");
                                // --- ---

                                customCalendarPicker.open();
                            }
                        }
                    }
                    // --- ---

                    // --- ПОЛЕ ДЛЯ ВРЕМЕНИ ---
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 3 // <-- Уменьшено
                        Label { text: "Время:"; font.pixelSize: 11 } // <-- Уменьшено
                        // Поле и кнопки для часов
                        ColumnLayout {
                            spacing: 1 // <-- Уменьшено
                            TextField {
                                id: actualStartTimeHoursField
                                Layout.preferredWidth: 40 // <-- Фиксированная ширина
                                placeholderText: "ЧЧ"
                                font.pixelSize: 11 // <-- Уменьшено
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 23 }
                                selectByMouse: true
                                horizontalAlignment: TextInput.AlignHCenter // Центрируем текст
                            }
                            RowLayout {
                                spacing: 1
                                Button {
                                    text: "▲"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualStartTimeHoursField, 1);
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualStartTimeHoursField, -1);
                                }
                            }
                        }
                        Text { text: ":"; font.pixelSize: 11 } // <-- Уменьшено
                        // Поле и кнопки для минут
                        ColumnLayout {
                            spacing: 1 // <-- Уменьшено
                            TextField {
                                id: actualStartTimeMinutesField
                                Layout.preferredWidth: 40 // <-- Фиксированная ширина
                                placeholderText: "ММ"
                                font.pixelSize: 11 // <-- Уменьшено
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 59 }
                                selectByMouse: true
                                horizontalAlignment: TextInput.AlignHCenter
                            }
                            RowLayout {
                                spacing: 1
                                Button {
                                    text: "▲"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualStartTimeMinutesField, 1);
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualStartTimeMinutesField, -1);
                                }
                            }
                        }
                        Text { text: ":"; font.pixelSize: 11 } // <-- Уменьшено
                        // Поле и кнопки для секунд
                        ColumnLayout {
                            spacing: 1 // <-- Уменьшено
                            TextField {
                                id: actualStartTimeSecondsField
                                Layout.preferredWidth: 40 // <-- Фиксированная ширина
                                placeholderText: "СС"
                                font.pixelSize: 11 // <-- Уменьшено
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 59 }
                                selectByMouse: true
                                horizontalAlignment: TextInput.AlignHCenter
                            }
                            RowLayout {
                                spacing: 1
                                Button {
                                    text: "▲"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualStartTimeSecondsField, 1);
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualStartTimeSecondsField, -1);
                                }
                            }
                        }
                    }
                    // --- ---
                }
                // --- ---

                // --- НОВОЕ: Ввод абсолютного фактического времени окончания (Дата + Время) ---
                Label {
                    text: "Окончание:*"
                    Layout.alignment: Qt.AlignRight
                    font.pixelSize: 11 // <-- Уменьшено
                    MouseArea {
                        id: endTimeTipMA_end
                        anchors.fill: parent
                        hoverEnabled: true
                    }
                    ToolTip {
                        text: "Фактическая абсолютная дата и время окончания выполнения действия"
                        visible: endTimeTipMA_end.containsMouse
                        delay: 500 // <-- Добавлено для ToolTip
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3 // <-- Уменьшено

                    // --- ПОЛЕ ДЛЯ ДАТЫ ---
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 3 // <-- Уменьшено
                        TextField {
                            id: actualEndDateField
                            Layout.fillWidth: true
                            // Layout.preferredWidth: 80 // <-- Можно задать фиксированную ширину, если нужно
                            placeholderText: "дд.ММ.гггг"
                            font.pixelSize: 11 // <-- Уменьшено
                            text: "" // Будет установлено в resetForAdd/loadDataForEdit
                            selectByMouse: true
                            readOnly: true // Только для чтения
                        }
                        Button {
                            id: actualEndDateCalendarButton
                            text: "📅"
                            font.pixelSize: 12 // <-- Уменьшено
                            Layout.preferredWidth: 30 // <-- Уменьшено
                            Layout.preferredHeight: 25 // <-- Уменьшено
                            onClicked: {
                                console.log("QML ActionExecutionEditorDialog: Нажата кнопка календаря для фактической даты окончания.");
                                // --- ИНИЦИАЛИЗАЦИЯ КАЛЕНДАРЯ ---
                                var currentDateText = actualEndDateField.text.trim();
                                var dateRegex = /^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[012])\.\d{4}$/;
                                if (dateRegex.test(currentDateText)) {
                                    var parts = currentDateText.split('.');
                                    var day = parseInt(parts[0], 10);
                                    var month = parseInt(parts[1], 10) - 1;
                                    var year = parseInt(parts[2], 10);
                                    var testDate = new Date(year, month, day);
                                    if (testDate.getDate() === day && testDate.getMonth() === month && testDate.getFullYear() === year) {
                                        customCalendarPicker.selectedDate = testDate;
                                        console.log("QML ActionExecutionEditorDialog: CustomCalendarPicker инициализирован датой из поля окончания:", testDate);
                                    } else {
                                        customCalendarPicker.selectedDate = new Date();
                                        console.log("QML ActionExecutionEditorDialog: CustomCalendarPicker инициализирован текущей датой (некорректная дата в поле окончания).");
                                    }
                                } else {
                                    customCalendarPicker.selectedDate = new Date();
                                    console.log("QML ActionExecutionEditorDialog: CustomCalendarPicker инициализирован текущей датой (некорректный формат в поле окончания).");
                                }
                                // --- ---

                                // --- ПОДКЛЮЧАЕМ ОБРАБОТЧИК ---
                                if (typeof endTimeCalendarConnection !== 'undefined' && endTimeCalendarConnection) {
                                    endTimeCalendarConnection.destroy();
                                }
                                endTimeCalendarConnection = Qt.createQmlObject(`
                                    import QtQuick 6.5;
                                    Connections {
                                        target: customCalendarPicker;
                                        function onDateSelected(date) {
                                            console.log("QML ActionExecutionEditorDialog: CustomCalendarPicker (Окончание): Дата выбрана:", date);
                                            var year = date.getFullYear();
                                            var month = String(date.getMonth() + 1).padStart(2, '0');
                                            var day = String(date.getDate()).padStart(2, '0');
                                            var formattedDate = day + "." + month + "." + year;
                                            actualEndDateField.text = formattedDate;
                                            console.log("QML ActionExecutionEditorDialog: CustomCalendarPicker (Окончание): Установлена новая дата в поле окончания:", formattedDate);
                                            if (typeof endTimeCalendarConnection !== 'undefined' && endTimeCalendarConnection) {
                                                endTimeCalendarConnection.destroy();
                                                endTimeCalendarConnection = undefined;
                                            }
                                        }
                                    }
                                `, actionExecutionEditorDialog, "endTimeCalendarConnectionDynamic");
                                // --- ---

                                customCalendarPicker.open();
                            }
                        }
                    }
                    // --- ---

                    // --- ПОЛЕ ДЛЯ ВРЕМЕНИ ---
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 3 // <-- Уменьшено
                        Label { text: "Время:"; font.pixelSize: 11 } // <-- Уменьшено
                        ColumnLayout {
                            spacing: 1 // <-- Уменьшено
                            TextField {
                                id: actualEndTimeHoursField
                                Layout.preferredWidth: 40 // <-- Фиксированная ширина
                                placeholderText: "ЧЧ"
                                font.pixelSize: 11 // <-- Уменьшено
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 23 }
                                selectByMouse: true
                                horizontalAlignment: TextInput.AlignHCenter
                            }
                            RowLayout {
                                spacing: 1
                                Button {
                                    text: "▲"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualEndTimeHoursField, 1);
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualEndTimeHoursField, -1);
                                }
                            }
                        }
                        Text { text: ":"; font.pixelSize: 11 } // <-- Уменьшено
                        ColumnLayout {
                            spacing: 1 // <-- Уменьшено
                            TextField {
                                id: actualEndTimeMinutesField
                                Layout.preferredWidth: 40 // <-- Фиксированная ширина
                                placeholderText: "ММ"
                                font.pixelSize: 11 // <-- Уменьшено
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 59 }
                                selectByMouse: true
                                horizontalAlignment: TextInput.AlignHCenter
                            }
                            RowLayout {
                                spacing: 1
                                Button {
                                    text: "▲"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualEndTimeMinutesField, 1);
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualEndTimeMinutesField, -1);
                                }
                            }
                        }
                        Text { text: ":"; font.pixelSize: 11 } // <-- Уменьшено
                        ColumnLayout {
                            spacing: 1 // <-- Уменьшено
                            TextField {
                                id: actualEndTimeSecondsField
                                Layout.preferredWidth: 40 // <-- Фиксированная ширина
                                placeholderText: "СС"
                                font.pixelSize: 11 // <-- Уменьшено
                                text: "00"
                                validator: IntValidator { bottom: 0; top: 59 }
                                selectByMouse: true
                                horizontalAlignment: TextInput.AlignHCenter
                            }
                            RowLayout {
                                spacing: 1
                                Button {
                                    text: "▲"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualEndTimeSecondsField, 1);
                                }
                                Button {
                                    text: "▼"
                                    font.pixelSize: 6 // <-- Уменьшено
                                    Layout.preferredWidth: 12 // <-- Уменьшено
                                    Layout.preferredHeight: 10 // <-- Уменьшено
                                    onClicked: incrementTimeComponentSimple(actualEndTimeSecondsField, -1);
                                }
                            }
                        }
                    }
                    // --- ---
                }
                // --- ---

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
                        console.log("QML ActionExecutionEditorDialog: FileDialog отчетных материалов: Приняты файлы:", reportMaterialsFileDialog.selectedFiles);
                        var selectedFileUrls = reportMaterialsFileDialog.selectedFiles; // Возвращает массив url в формате file:///
                        if (selectedFileUrls && selectedFileUrls.length > 0) {
                            var pathsToAdd = [];
                            for (var i = 0; i < selectedFileUrls.length; i++) {
                                var fileUrl = selectedFileUrls[i];
                                if (fileUrl) {
                                    // Преобразуем URL в локальный путь (удаляем file:///)
                                    var localPath = fileUrl.toString().replace(/^file:[\/\\]{2,3}/, ""); // Убирает file:/// или file:\\
                                    console.log("QML ActionExecutionEditorDialog: FileDialog отчетных материалов: Локальный путь:", localPath);
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
                        console.log("QML ActionExecutionEditorDialog: FileDialog отчетных материалов: Отменен пользователем.");
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
                            console.log("QML ActionExecutionEditorDialog: Нажата кнопка 'Добавить файл...' для отчетных материалов");
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
                    console.log("QML ActionExecutionEditorDialog: Нажата кнопка Отмена");
                    actionExecutionEditorDialog.close();
                }
            }
            Button {
                text: "Сохранить"
                onClicked: {
                    console.log("QML ActionExecutionEditorDialog: Нажата кнопка Сохранить");
                    errorMessageLabel.text = "";

                    // --- ВАЛИДАЦИЯ ОПИСАНИЯ ---
                    if (!descriptionArea.text.trim()) {
                        errorMessageLabel.text = "Пожалуйста, заполните описание действия.";
                        return;
                    }

                    // --- СБОРКА СТРОКИ ДАТЫ И ВРЕМЕНИ ИЗ РАЗДЕЛЬНЫХ ПОЛЕЙ ---
                    function buildDateTimeString(dateField, hField, mField, sField) {
                        var d = dateField.text.trim();
                        var h = hField.text.trim();
                        var m = mField.text.trim();
                        var s = sField.text.trim();
                        if (!d || !h || !m || !s) return "";
                        return d + " " + h + ":" + m + ":" + s;
                    }

                    var startDateTimeStr = buildDateTimeString(
                        actualStartDateField,
                        actualStartTimeHoursField,
                        actualStartTimeMinutesField,
                        actualStartTimeSecondsField
                    );

                    var endDateTimeStr = buildDateTimeString(
                        actualEndDateField,
                        actualEndTimeHoursField,
                        actualEndTimeMinutesField,
                        actualEndTimeSecondsField
                    );

                    // --- ВАЛИДАЦИЯ ФОРМАТА ---
                    var dateTimeRegex = /^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[012])\.\d{4} ([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$/;
                    if (!startDateTimeStr || !dateTimeRegex.test(startDateTimeStr)) {
                        errorMessageLabel.text = "Некорректный формат времени начала. Используйте дд.ММ.гггг чч:мм:сс.";
                        return;
                    }
                    if (!endDateTimeStr || !dateTimeRegex.test(endDateTimeStr)) {
                        errorMessageLabel.text = "Некорректный формат времени окончания. Используйте дд.ММ.гггг чч:мм:сс.";
                        return;
                    }

                    // --- ПАРСИНГ И СРАВНЕНИЕ ---
                    function parseDateTime(dtStr) {
                        var parts = dtStr.split(/[\s.:]+/);
                        if (parts.length !== 6) return null;
                        var day = parseInt(parts[0], 10);
                        var month = parseInt(parts[1], 10) - 1;
                        var year = parseInt(parts[2], 10);
                        var hour = parseInt(parts[3], 10);
                        var min = parseInt(parts[4], 10);
                        var sec = parseInt(parts[5], 10);
                        var date = new Date(year, month, day, hour, min, sec);
                        if (date.getDate() !== day || date.getMonth() !== month || date.getFullYear() !== year) return null;
                        return date;
                    }

                    var startObj = parseDateTime(startDateTimeStr);
                    var endObj = parseDateTime(endDateTimeStr);
                    if (!startObj || !endObj) {
                        errorMessageLabel.text = "Ошибка в дате/времени начала или окончания.";
                        return;
                    }
                    if (endObj < startObj) {
                        errorMessageLabel.text = "Время окончания не может быть меньше времени начала.";
                        return;
                    }

                    // --- СОБИРАЕМ ДАННЫЕ ДЛЯ PYTHON ---
                    // ВАЖНО: Используем calculated_* вместо actual_*
                    var actionExecutionData = {
                        "snapshot_description": descriptionArea.text.trim(),
                        "snapshot_technical_text": technicalTextArea.text.trim(),
                        "calculated_start_time": startDateTimeStr,   // ← ключ изменён!
                        "calculated_end_time": endDateTimeStr,       // ← ключ изменён!
                        "snapshot_contact_phones": contactPhonesField.text,
                        "snapshot_report_materials": reportMaterialsArea.text,
                        "reported_to": reportedToField.text,
                        "notes": notesArea.text
                    };

                    // --- ОТПРАВКА В PYTHON ---
                    var result;
                    if (actionExecutionEditorDialog.isEditMode && actionExecutionEditorDialog.currentActionExecutionId > 0) {
                        console.log("QML ActionExecutionEditorDialog: Обновление action_execution ID", currentActionExecutionId, "в Python:", JSON.stringify(actionExecutionData));
                        result = appData.updateActionExecution(currentActionExecutionId, actionExecutionData);
                    } else if (!actionExecutionEditorDialog.isEditMode && actionExecutionEditorDialog.executionId > 0) {
                        console.log("QML ActionExecutionEditorDialog: Добавление нового action_execution для execution ID", executionId, "в Python:", JSON.stringify(actionExecutionData));
                        result = appData.addActionExecution(executionId, actionExecutionData);
                    } else {
                        errorMessageLabel.text = "Ошибка состояния диалога.";
                        console.error("QML ActionExecutionEditorDialog: Недостаточно данных для сохранения.");
                        return;
                    }

                    if (result === true || (typeof result === 'number' && result > 0)) {
                        console.log("QML ActionExecutionEditorDialog: Успешно сохранено.");
                        actionExecutionEditorDialog.actionExecutionSaved();
                        actionExecutionEditorDialog.close();
                    } else {
                        var errorMsg = typeof result === 'string' ? result : "Неизвестная ошибка";
                        errorMessageLabel.text = "Ошибка: " + errorMsg;
                        console.warn("QML ActionExecutionEditorDialog: Ошибка при сохранении:", errorMsg);
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
        console.log("QML ActionExecutionEditorDialog: Сброс для добавления");
        isEditMode = false;
        currentActionExecutionId = -1;
        descriptionArea.text = "";
        contactPhonesField.text = "";
        reportMaterialsArea.text = "";
        technicalTextArea.text = "";
        reportedToField.text = "";
        notesArea.text = "";
        errorMessageLabel.text = "";
        dialogTitleLabel.text = "Добавить новое действие";

        // Установка текущей даты/времени
        var now = new Date();
        var d = String(now.getDate()).padStart(2, '0');
        var m = String(now.getMonth() + 1).padStart(2, '0');
        var y = now.getFullYear();
        var h = String(now.getHours()).padStart(2, '0');
        var min = String(now.getMinutes()).padStart(2, '0');
        var s = String(now.getSeconds()).padStart(2, '0');

        actualStartDateField.text = `${d}.${m}.${y}`;
        actualStartTimeHoursField.text = h;
        actualStartTimeMinutesField.text = min;
        actualStartTimeSecondsField.text = s;

        actualEndDateField.text = `${d}.${m}.${y}`;
        actualEndTimeHoursField.text = h;
        actualEndTimeMinutesField.text = min;
        actualEndTimeSecondsField.text = s;
    }

    /**
    * Загружает данные action_execution для редактирования
    */
    function loadDataForEdit(actionExecutionData) {
        console.log("QML ActionExecutionEditorDialog: Загрузка данных:", JSON.stringify(actionExecutionData));
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
        dialogTitleLabel.text = "Редактировать действие";

        // Вспомогательная функция разбора даты
        function setDateTimeFields(dateTimeStr, dateField, hField, mField, sField) {
            if (!dateTimeStr) {
                dateField.text = "";
                hField.text = "00";
                mField.text = "00";
                sField.text = "00";
                return;
            }

            var match1 = dateTimeStr.match(/^(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2}):(\d{2})$/);
            var match2 = dateTimeStr.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);

            if (match1) {
                dateField.text = match1[1] + "." + match1[2] + "." + match1[3];
                hField.text = match1[4];
                mField.text = match1[5];
                sField.text = match1[6];
            } else if (match2) {
                dateField.text = match2[3] + "." + match2[2] + "." + match2[1];
                hField.text = match2[4];
                mField.text = match2[5];
                sField.text = match2[6];
            } else {
                dateField.text = "";
                hField.text = "00";
                mField.text = "00";
                sField.text = "00";
            }
        }

        // Загружаем calculated_* как фактические времена
        setDateTimeFields(
            actionExecutionData.calculated_start_time,
            actualStartDateField,
            actualStartTimeHoursField,
            actualStartTimeMinutesField,
            actualStartTimeSecondsField
        );

        setDateTimeFields(
            actionExecutionData.calculated_end_time,
            actualEndDateField,
            actualEndTimeHoursField,
            actualEndTimeMinutesField,
            actualEndTimeSecondsField
        );
    }

    function incrementTimeComponentSimple(textField, delta) {
        console.log("QML ActionExecutionEditorDialog: incrementTimeComponentSimple called with", textField, delta);
        var text = textField.text || "00";
        console.log("QML ActionExecutionEditorDialog: Current text:", text);

        var value = parseInt(text, 10) || 0;
        console.log("QML ActionExecutionEditorDialog: Parsed value:", value);

        value += delta;

        // Обработка ограничений в зависимости от типа компонента (часы/минуты/секунды)
        // Предполагаем, что ID текстового поля содержит тип (hours, minutes, seconds)
        var fieldName = textField.objectName || ""; // Можно использовать objectName для идентификации
        if (textField === actualStartTimeHoursField || textField === actualEndTimeHoursField) {
            // Ограничиваем диапазон 0-23 для часов
            value = (value + 24) % 24; // Обеспечивает корректное переполнение
        } else if (textField === actualStartTimeMinutesField || textField === actualEndTimeMinutesField ||
                   textField === actualStartTimeSecondsField || textField === actualEndTimeSecondsField) {
            // Ограничиваем диапазон 0-59 для минут и секунд
            value = (value + 60) % 60; // Обеспечивает корректное переполнение
        } else {
            // По умолчанию, если не определён тип, просто ограничиваем 0-59
            value = Math.max(0, Math.min(59, value));
        }

        // Форматируем обратно в строку HH, MM, SS
        var newText = value.toString().padStart(2, '0');

        console.log("QML ActionExecutionEditorDialog: New text:", newText);
        textField.text = newText;
    }

    onOpened: {
        console.log("QML ActionExecutionEditorDialog: Диалог открыт. Режим:", isEditMode ? "Редактирование" : "Добавление");
        errorMessageLabel.text = "";
        // Фокус на первое поле
        if (isEditMode) {
            descriptionArea.forceActiveFocus();
        } else {
            // При добавлении тоже фокус на описание
            descriptionArea.forceActiveFocus();
        }
    }
    // --- ---
        // Добавлен в конец ActionExecutionEditorDialog.qml
    CustomCalendarPicker {
        id: customCalendarPicker
        // visible: false // Обычно Popup сам управляет видимостью, но можно явно скрыть
        // anchors.fill: parent // Обычно не нужно для Popup/Dialog
        // z: -1 // Можно поместить позади, если нужно, но обычно Popup выше
    }
    // --- ---
}

