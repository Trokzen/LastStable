// ui/SettingsView.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5
import QtQuick.Dialogs 6.5
// --- Импорт для OfficerEditorDialog ---
import "." // Импорт из той же директории (ui/)
// --- ---

Item {
    id: settingsViewRoot

    // --- Основной столбец для размещения вкладок и содержимого ---
    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        // --- Панель вкладок настроек ---
        TabBar {
            id: settingsTabBar
            Layout.fillWidth: true

            // --- Вкладка 1: Пост ---
            TabButton {
                text: "Пост"
            }
            // --- Вкладка 2: Должностные лица ---
            TabButton {
                text: "Должностные лица"
            }
            // --- Вкладка 3: Мероприятия ---
            TabButton {
                text: "Алгоритмы"
            }
            // --- Вкладка 4: Организации ---
            TabButton {
                text: "Организации"
            }
        }

        // --- Содержимое вкладок ---
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: settingsTabBar.currentIndex

            onCurrentIndexChanged: {
                console.log("QML SettingsView: Переключение на вкладку", currentIndex)
                // При переключении на вкладку Организаций загружаем данные
                if (currentIndex === 3 && organizationsListView) {
                    console.log("QML SettingsView: Загрузка организаций...")
                    organizationsListView.loadOrganizations()
                }
            }

            // --- Вкладка 1: Пост (с перенесенными настройками) ---
            Item {
                id: workplaceTab
                
                // Основной столбец для содержимого вкладки
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 15

                    Label {
                        text: "Настройки поста"
                        font.pointSize: 14
                        font.bold: true
                    }

                    // --- ScrollView для прокручиваемой части ---
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true  // Занимает всё доступное пространство кроме кнопки
                        clip: true
                        
                        ColumnLayout {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            spacing: 15

                            // --- Поля для "Пост" ---
                            Label {
                                text: "Номер поста:"
                            }
                            TextField {
                                id: postNumberField
                                Layout.fillWidth: true
                                placeholderText: "Введите номер поста..."
                            }

                            Label {
                                text: "Название поста:"
                            }
                            TextField {
                                id: postNameField
                                Layout.fillWidth: true
                                placeholderText: "Введите название поста..."
                            }
                            
                            Label {
                                text: "Название рабочего места:"
                            }
                            TextField {
                                id: workplaceNameField
                                Layout.fillWidth: true
                                placeholderText: "Введите название рабочего места..."
                            }
                            // --- ---

                            // --- Перенесенные настройки из "Организации" ---

                            // Настройки напоминаний
                            CheckBox {
                                id: persistentRemindersCheckBox
                                text: "Использовать настойчивые напоминания"
                            }

                            // Настройки звука
                            CheckBox {
                                id: soundEnabledCheckBox
                                text: "Включить звуковой сигнал"
                            }

                            // Коррекция времени
                            GroupBox {
                                title: "Коррекция времени и даты"
                                Layout.fillWidth: true
                                ColumnLayout {
                                    // --- Название местного времени ---
                                    Label {
                                        text: "Название местного времени:"
                                    }
                                    TextField {
                                        id: customTimeLabelField
                                        Layout.fillWidth: true
                                        placeholderText: "Например: Местное время, Свердловское..."
                                        // text будет установлен в loadSettings
                                    }
                                    // --- ---
                                    
                                    // --- Смещение местного времени (часы) ---
                                    Label {
                                        text: "Смещение местного времени от системного (часы):"
                                        ToolTip.text: "Положительное значение - время вперёд, отрицательное - назад. Например, -2 для Калининграда, +2 для Самары относительно Москвы."
                                        ToolTip.visible: hovered
                                    }
                                    // Используем SpinBox для ввода целого числа со смещением
                                    SpinBox {
                                        id: customTimeOffsetSpinBox
                                        Layout.fillWidth: true
                                        from: -24 // Разумный диапазон
                                        to: 24
                                        stepSize: 1
                                        // value будет установлен в loadSettings
                                        // Добавим суффикс " ч" для наглядности
                                        property string suffix: " ч"
                                        textFromValue: function(value) { return value + suffix; }
                                        valueFromText: function(text) { return parseInt(text.replace(suffix, '')) || 0; }
                                    }
                                    // --- ---
                                    
                                    // --- Показывать московское время ---
                                    CheckBox {
                                        id: showMoscowTimeCheckBox
                                        text: "Показывать московское время"
                                        // checked будет установлен в loadSettings
                                    }
                                    // --- ---
                                    
                                    // --- Смещение московского времени (часы) ---
                                    // (Отображается, если включена опция показа)
                                    ColumnLayout {
                                        visible: showMoscowTimeCheckBox.checked
                                        spacing: 5
                                        
                                        Label {
                                            text: "Смещение московского времени от системного (часы):"
                                            ToolTip.text: "Обычно 0. Укажите, если нужно скорректировать показ Москвы."
                                            ToolTip.visible: hovered
                                        }
                                        SpinBox {
                                            id: moscowTimeOffsetSpinBox
                                            Layout.fillWidth: true
                                            from: -24
                                            to: 24
                                            stepSize: 1
                                            // value будет установлен в loadSettings
                                            property string suffix: " ч"
                                            textFromValue: function(value) { return value + suffix; }
                                            valueFromText: function(text) { return parseInt(text.replace(suffix, '')) || 0; }
                                        }
                                    }
                                    // --- ---
                                }
                            }

                            // Настройки внешнего вида
                            // --- FileDialog для выбора эмблемы ---
                            FileDialog {
                                id: emblemFileDialog
                                title: "Выберите файл эмблемы"
                                // Ограничиваем выбор только изображениями
                                nameFilters: ["Изображения (*.png *.jpg *.jpeg *.bmp *.gif *.svg)"]
                                // Выбираем один файл
                                fileMode: FileDialog.OpenFile
                                onAccepted: {
                                    console.log("QML SettingsView: FileDialog (эмблема) принят. Выбранный файл:", selectedFile)
                                    // Обновляем путь к эмблеме в поле ввода
                                    // selectedFile - это URL вида "file:///path/to/image.png"
                                    // Нам нужен локальный путь
                                    var localPath = selectedFile.toString()
                                    if (localPath.startsWith("file:///")) {
                                        // Для Windows убираем "file:///", для других ОС может потребоваться другая обработка
                                        localPath = localPath.substring(8)
                                    }
                                    backgroundImagePathField.text = localPath
                                    console.log("QML SettingsView: Установлен путь к эмблеме:", localPath)
                                }
                                onRejected: {
                                    console.log("QML SettingsView: FileDialog (эмблема) отклонен")
                                }
                            }
                            // --- ---

                            // --- Обновленная группа "Внешний вид" ---
                            GroupBox {
                                title: "Внешний вид"
                                Layout.fillWidth: true
                                ColumnLayout {
                                    // --- Эмблема ---
                                    Label {
                                        text: "Фоновое изображение (эмблема):"
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 10
                                        
                                        Button {
                                            text: "Выбрать файл..."
                                            onClicked: {
                                                console.log("QML SettingsView: Нажата кнопка 'Выбрать файл...' для эмблемы")
                                                emblemFileDialog.open()
                                            }
                                        }
                                        
                                        // Поле для отображения пути к файлу
                                        TextField {
                                            id: backgroundImagePathField
                                            Layout.fillWidth: true
                                            placeholderText: "Путь к файлу эмблемы..."
                                            readOnly: true // Сделаем поле только для чтения, чтобы путь нельзя было испортить вручную
                                            // text будет установлен в loadSettings
                                        }
                                        
                                        // Предварительный просмотр эмблемы
                                        Image {
                                            id: emblemPreview
                                            source: backgroundImagePathField.text ? "file:///" + backgroundImagePathField.text : "../resources/images/placeholder_emblem.png"
                                            fillMode: Image.PreserveAspectFit
                                            // Установим максимальные размеры для предпросмотра
                                            Layout.preferredWidth: 50
                                            Layout.preferredHeight: 50
                                            // Обновляем источник при изменении пути
                                            Binding {
                                                target: emblemPreview
                                                property: "source"
                                                value: backgroundImagePathField.text ? "file:///" + backgroundImagePathField.text : "../resources/images/placeholder_emblem.png"
                                            }
                                        }
                                    }
                                    // --- ---
                                    
                                    // --- Шрифт интерфейса ---
                                    Label {
                                        text: "Шрифт интерфейса:"
                                    }
                                    ComboBox {
                                        id: fontFamilyComboBox
                                        // --- НОВОЕ: Динамическое заполнение шрифтами системы ---
                                        // Qt.fontFamilies() возвращает список доступных шрифтов в системе
                                        model: Qt.fontFamilies() 
                                        // --- ---
                                        // currentIndex и text будут установлены в loadSettings
                                        // --- Добавим подсказку ---
                                        ToolTip.text: "Выберите шрифт для интерфейса приложения"
                                        ToolTip.visible: hovered
                                        Layout.preferredWidth: 150
                                        // --- ---
                                    }
                                    // --- ---
                                    
                                    // --- Размер шрифта интерфейса ---
                                    Label {
                                        text: "Размер шрифта интерфейса:"
                                    }
                                    SpinBox {
                                        id: fontSizeSpinBox
                                        from: 8
                                        to: 24
                                        value: 12 // Значение по умолчанию, будет обновлено в loadSettings
                                        Layout.preferredWidth: 150
                                    }
                                    // --- ---
                                    
                                    // --- Начертание шрифта интерфейса ---
                                    Label {
                                        text: "Начертание шрифта интерфейса:"
                                    }
                                    ComboBox {
                                        id: fontStyleComboBox
                                        Layout.preferredWidth: 150
                                        // Модель с описаниями и значениями
                                        model: ListModel {
                                            ListElement { name: "Обычный"; value: "normal" }
                                            ListElement { name: "Жирный"; value: "bold" }
                                            ListElement { name: "Курсив"; value: "italic" }
                                            ListElement { name: "Жирный курсив"; value: "bold_italic" }
                                        }
                                        textRole: "name" // Отображаем поле 'name'
                                        // currentIndex будет установлен в loadSettings
                                    }
                                    // --- ---
                                    
                                    // --- Цвет фона ---
                                    Label {
                                        text: "Цвет фона:"
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 30
                                        color: backgroundColorField.text || "#ecf0f1" // Цвет из поля ввода или по умолчанию
                                        border.color: "black"
                                        radius: 5
                                        visible: false
                                        
                                        // Отображение hex-кода цвета поверх прямоугольника
                                        Text {
                                            anchors.centerIn: parent
                                            text: backgroundColorField.text || "#ecf0f1"
                                            color: "black" // Можно сделать динамическим в зависимости от яркости фона
                                            font.pixelSize: 12
                                        }
                                        
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                console.log("QML SettingsView: Нажат цветовой прямоугольник. Текущий цвет:", backgroundColorField.text)
                                                // TODO: Открыть диалог выбора цвета (ColorDialog)
                                                // Пока просто покажем сообщение
                                                showInfoMessage("Выбор цвета (TODO): " + (backgroundColorField.text || "#ecf0f1"))
                                            }
                                        }
                                    }
                                    TextField {
                                        id: backgroundColorField
                                        visible: false
                                        Layout.fillWidth: true
                                        placeholderText: "Введите HEX-код цвета (например, #ecf0f1)..."
                                        // text будет установлен в loadSettings
                                        // Добавим валидацию HEX-кода
                                        // validator: RegExpValidator { regExp: /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/ }
                                    }
                                    // --- ---
                                    GroupBox {
                                        title: "Предпросмотр шрифта интерфейса"
                                        Layout.fillWidth: true
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 5
                                            spacing: 5

                                            Text {
                                                Layout.fillWidth: true
                                                // --- ДИНАМИЧЕСКОЕ ПРИМЕНЕНИЕ СТИЛЯ ШРИФТА ---
                                                // text: "Пример текста для предпросмотра шрифта интерфейса" // <-- СТАРОЕ
                                                text: {
                                                    // Формируем пример текста, отражающий текущие настройки
                                                    var fontFamily = fontFamilyComboBox.currentText || "Arial";
                                                    var fontSize = fontSizeSpinBox.value || 12;
                                                    var fontStyleDesc = "Обычный";
                                                    // Получаем описание стиля из модели fontStyleComboBox
                                                    if (fontStyleComboBox.currentIndex !== -1 && fontStyleComboBox.model.get(fontStyleComboBox.currentIndex)) {
                                                        fontStyleDesc = fontStyleComboBox.model.get(fontStyleComboBox.currentIndex).name || "Обычный";
                                                    }
                                                    return "Пример текста (" + fontFamily + ", " + fontSize + "pt, " + fontStyleDesc + ")";
                                                }
                                                // --- ---
                                                // --- ДИНАМИЧЕСКОЕ ПРИМЕНЕНИЕ СВОЙСТВ ШРИФТА ---
                                                font.family: fontFamilyComboBox.currentText || "Arial" // Применяем выбранный шрифт
                                                font.pixelSize: (fontSizeSpinBox.value || 12) * scaleFactor // Применяем выбранный размер
                                                // Применяем выбранный стиль
                                                font.bold: {
                                                    // Получаем значение 'value' из выбранного элемента модели
                                                    var styleValue = "normal";
                                                    if (fontStyleComboBox.currentIndex !== -1 && fontStyleComboBox.model.get(fontStyleComboBox.currentIndex)) {
                                                        styleValue = fontStyleComboBox.model.get(fontStyleComboBox.currentIndex).value || "normal";
                                                    }
                                                    return (styleValue === "bold" || styleValue === "bold_italic");
                                                }
                                                font.italic: {
                                                    // Получаем значение 'value' из выбранного элемента модели
                                                    var styleValue = "normal";
                                                    if (fontStyleComboBox.currentIndex !== -1 && fontStyleComboBox.model.get(fontStyleComboBox.currentIndex)) {
                                                        styleValue = fontStyleComboBox.model.get(fontStyleComboBox.currentIndex).value || "normal";
                                                    }
                                                    return (styleValue === "italic" || styleValue === "bold_italic");
                                                }
                                                // --- ---
                                                wrapMode: Text.WordWrap
                                                elide: Text.ElideRight
                                            }
                                            // --- ---
                                        }
                                    }


                                }
                            }
                            
                            // --- НОВЫЙ БЛОК: Шрифт для печати ---
                            GroupBox {
                                title: "Шрифт для печати"
                                Layout.fillWidth: true
                                ColumnLayout {
                                    // --- Поля для настройки шрифта печати ---
                                    Label {
                                        text: "Шрифт интерфейса печати:"
                                    }
                                    ComboBox {
                                        id: printFontFamilyComboBox
                                        // --- НОВОЕ: Динамическое заполнение шрифтами системы ---
                                        // Qt.fontFamilies() возвращает список доступных шрифтов в системе
                                        model: Qt.fontFamilies()
                                        // --- ---
                                        // currentIndex и text будут установлены в loadSettings
                                        // --- Добавим подсказку ---
                                        ToolTip.text: "Выберите шрифт для печатных форм и отчетов"
                                        ToolTip.visible: hovered
                                        Layout.preferredWidth: 150
                                        // --- ---
                                    }

                                    Label {
                                        text: "Размер шрифта печати:"
                                    }
                                    SpinBox {
                                        id: printFontSizeSpinBox
                                        from: 3
                                        to: 72 // Можно увеличить диапазон
                                        value: 12 // Значение по умолчанию, будет обновлено в loadSettings
                                        Layout.preferredWidth: 150
                                    }
                                    // --- НОВОЕ: Начертание шрифта печати ---
                                    Label {
                                        text: "Начертание шрифта печати:"
                                    }
                                    ComboBox {
                                        id: printFontStyleComboBox
                                        Layout.preferredWidth: 150
                                        // Модель с описаниями и значениями для начертания
                                        model: ListModel {
                                            ListElement { name: "Обычный"; value: "normal" }
                                            ListElement { name: "Жирный"; value: "bold" }
                                            ListElement { name: "Курсив"; value: "italic" }
                                            ListElement { name: "Жирный курсив"; value: "bold_italic" }
                                        }
                                        textRole: "name" // Отображаем поле 'name'
                                        // currentIndex будет установлен в loadSettings
                                    }

                                    GroupBox {
                                        title: "Предпросмотр шрифта печати"
                                        Layout.fillWidth: true
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 5
                                            spacing: 5

                                            Text {
                                                Layout.fillWidth: true
                                                // --- ДИНАМИЧЕСКОЕ ПРИМЕНЕНИЕ СТИЛЯ ШРИФТА ---
                                                // text: "Пример текста для предпросмотра шрифта печати" // <-- СТАРОЕ
                                                text: {
                                                    // Формируем пример текста, отражающий текущие настройки
                                                    var fontFamily = printFontFamilyComboBox.currentText || "Arial";
                                                    var fontSize = printFontSizeSpinBox.value || 12;
                                                    var fontStyleDesc = "Обычный";
                                                    // Получаем описание стиля из модели printFontStyleComboBox
                                                    if (printFontStyleComboBox.currentIndex !== -1 && printFontStyleComboBox.model.get(printFontStyleComboBox.currentIndex)) {
                                                        fontStyleDesc = printFontStyleComboBox.model.get(printFontStyleComboBox.currentIndex).name || "Обычный";
                                                    }
                                                    return "Пример текста печати (" + fontFamily + ", " + fontSize + "pt, " + fontStyleDesc + ")";
                                                }
                                                // --- ---
                                                // --- ДИНАМИЧЕСКОЕ ПРИМЕНЕНИЕ СВОЙСТВ ШРИФТА ---
                                                font.family: printFontFamilyComboBox.currentText || "Arial" // Применяем выбранный шрифт печати
                                                font.pixelSize: (printFontSizeSpinBox.value || 12) * scaleFactor // Применяем выбранный размер печати
                                                // Применяем выбранный стиль печати
                                                font.bold: {
                                                    // Получаем значение 'value' из выбранного элемента модели
                                                    var styleValue = "normal";
                                                    if (printFontStyleComboBox.currentIndex !== -1 && printFontStyleComboBox.model.get(printFontStyleComboBox.currentIndex)) {
                                                        styleValue = printFontStyleComboBox.model.get(printFontStyleComboBox.currentIndex).value || "normal";
                                                    }
                                                    return (styleValue === "bold" || styleValue === "bold_italic");
                                                }
                                                font.italic: {
                                                    // Получаем значение 'value' из выбранного элемента модели
                                                    var styleValue = "normal";
                                                    if (printFontStyleComboBox.currentIndex !== -1 && printFontStyleComboBox.model.get(printFontStyleComboBox.currentIndex)) {
                                                        styleValue = printFontStyleComboBox.model.get(printFontStyleComboBox.currentIndex).value || "normal";
                                                    }
                                                    return (styleValue === "italic" || styleValue === "bold_italic");
                                                }
                                                // --- ---
                                                wrapMode: Text.WordWrap
                                                elide: Text.ElideRight
                                            }
                                            // --- ---
                                        }
                                    }
                                    // --- ---

                                }
                            }
                            // --- ---

                            // Заполнитель для правильного скроллинга
                            Item {
                                Layout.fillHeight: true
                            }
                        }
                    }
                    // --- Конец ScrollView ---

                    // Кнопка сохранения - ВНЕ ScrollView, всегда видна!
                    Button {
                        text: "Сохранить"
                        onClicked: {
                            console.log("QML: Нажата кнопка сохранить");
                            saveSettings();
                        }
                        Layout.alignment: Qt.AlignRight
                    }
                }
            }

            // --- Вкладка 2: Должностные лица ---
            Item {
                id: officersTab
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 10

                    Label {
                        text: "Список должностных лиц"
                        font.pointSize: 14
                        font.bold: true
                    }

                    // Панель с кнопками управления
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Rectangle {
                            Layout.preferredWidth: 110
                            Layout.preferredHeight: 36
                            radius: 8
                            color: {
                                if (addOfficerBtn.pressed) return "#218c3d"
                                if (addOfficerBtn.hovered) return "#2ecc71"
                                return "#27ae60"
                            }
                            Behavior on color { ColorAnimation { duration: 150 } }
                            MouseArea {
                                id: addOfficerBtn
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    officerEditorDialog.resetForAdd()
                                    officerEditorDialog.open()
                                }
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "➕ Добавить"
                                color: "#ffffff"
                                font.pixelSize: 13
                                font.bold: true
                            }
                        }
                        Rectangle {
                            Layout.preferredWidth: 130
                            Layout.preferredHeight: 36
                            radius: 8
                            color: {
                                if (editOfficerBtn.pressed) return "#c9951d"
                                if (editOfficerBtn.hovered) return "#f39c12"
                                return "#f1c40f"
                            }
                            Behavior on color { ColorAnimation { duration: 150 } }
                            opacity: officersListView.currentIndex !== -1 ? 1.0 : 0.5
                            MouseArea {
                                id: editOfficerBtn
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                enabled: officersListView.currentIndex !== -1
                                onClicked: {
                                    var selectedIndex = officersListView.currentIndex
                                    if (selectedIndex !== -1) {
                                        var officerData = officersListView.model.get(selectedIndex)
                                        officerEditorDialog.loadDataForEdit(officerData)
                                        officerEditorDialog.open()
                                    }
                                }
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "✏️ Редактировать"
                                color: "#2c3e50"
                                font.pixelSize: 13
                                font.bold: true
                            }
                        }
                        Rectangle {
                            Layout.preferredWidth: 110
                            Layout.preferredHeight: 36
                            radius: 8
                            color: {
                                if (delOfficerBtn.pressed) return "#c0392b"
                                if (delOfficerBtn.hovered) return "#e74c3c"
                                return "#e8453c"
                            }
                            Behavior on color { ColorAnimation { duration: 150 } }
                            opacity: officersListView.currentIndex !== -1 ? 1.0 : 0.5
                            MouseArea {
                                id: delOfficerBtn
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                enabled: officersListView.currentIndex !== -1
                                onClicked: {
                                    var selectedIndex = officersListView.currentIndex
                                    if (selectedIndex !== -1) {
                                        var officerData = officersListView.model.get(selectedIndex)
                                        var result = appData.deleteDutyOfficer(officerData.id)
                                        if (result === true || (typeof result === 'number' && result > 0)) {
                                            settingsViewRoot.loadDutyOfficers()
                                        }
                                    }
                                }
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "🗑️ Удалить"
                                color: "#ffffff"
                                font.pixelSize: 13
                                font.bold: true
                            }
                        }
                        // Заполнитель
                        Item {
                            Layout.fillWidth: true
                        }
                        // Кнопка обновления списка (на случай, если данные изменились вне этого окна)
                        Rectangle {
                            Layout.preferredWidth: 110
                            Layout.preferredHeight: 36
                            radius: 8
                            color: {
                                if (refreshOfficerBtn.pressed) return "#2980b9"
                                if (refreshOfficerBtn.hovered) return "#3498db"
                                return "#5dade2"
                            }
                            Behavior on color { ColorAnimation { duration: 150 } }
                            MouseArea {
                                id: refreshOfficerBtn
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: settingsViewRoot.loadDutyOfficers()
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "🔄 Обновить"
                                color: "#ffffff"
                                font.pixelSize: 13
                                font.bold: true
                            }
                        }
                    }

                    // Список должностных лиц
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        ListView {
                            id: officersListView
                            clip: true // Обрезаем содержимое, выходящее за границы
                            model: ListModel {
                                id: officersListModel
                                // Модель будет заполнена данными из Python
                            }
                            delegate: Rectangle {
                                width: ListView.view.width
                                height: 40
                                color: index % 2 ? "#f9f9f9" : "#ffffff" // Чередующийся цвет
                                border.color: officersListView.currentIndex === index ? "#3498db" : "#ddd" // Выделение выбранного
                                Text {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 10
                                    anchors.verticalCenter: parent.verticalCenter
                                    // Формируем строку отображения: Звание Фамилия И.О.
                                    text: model.rank + " " + model.last_name + " " +
                                          model.first_name.charAt(0) + "." +
                                          (model.middle_name ? model.middle_name.charAt(0) + "." : "")
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        officersListView.currentIndex = index; // Устанавливаем выбранный элемент
                                    }
                                }
                            }
                        }
                    }
                }

                // --- OfficerEditorDialog для добавления/редактирования ---
                OfficerEditorDialog {
                    id: officerEditorDialog
                    // Подключаемся к сигналу accepted, чтобы перезагрузить список после успешной операции
                    onAccepted: {
                        console.log("QML SettingsView: Получен сигнал accepted от OfficerEditorDialog. Перезагружаем список.");
                        settingsViewRoot.loadDutyOfficers();
                    }
                }
                // --- ---
            }

            // --- Вкладка 3: Алгоритмы ---
            Item {
                id: algorithmsTab
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 10
                    
                    // Импортируем наш новый компонент
                    AlgorithmsListView {
                        id: algorithmsListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        
                        // Подключаем сигналы
                        onAddAlgorithmRequested: {
                            console.log("QML SettingsView: Запрошено добавление алгоритма")
                            algorithmEditorDialog.resetForAdd()
                            algorithmEditorDialog.open()
                        }
                        
                        onEditAlgorithmRequested: {
                            console.log("QML SettingsView: Запрошено редактирование алгоритма:", algorithmData)
                            algorithmEditorDialog.loadDataForEdit(algorithmData)
                            algorithmEditorDialog.open()
                        }
                        
                        onDeleteAlgorithmRequested: {
                            console.log("QML SettingsView: Запрошено удаление алгоритма ID:", algorithmId)
                            // TODO: Добавить подтверждение
                            var confirmDelete = true // Пока без подтверждения
                            if (confirmDelete) {
                                var result = appData.deleteAlgorithm(algorithmId)
                                if (result === true) {
                                    console.log("QML SettingsView: Алгоритм ID", algorithmId, "удален успешно.")
                                    // Обновляем список в ListView
                                    algorithmsListView.removeAlgorithm(algorithmId)
                                } else if (typeof result === 'string') {
                                    console.warn("QML SettingsView: Ошибка удаления алгоритма:", result)
                                    // TODO: Отобразить ошибку пользователю
                                } else {
                                    console.error("QML SettingsView: Неизвестная ошибка удаления алгоритма. Результат:", result)
                                }
                            }
                        }
                        
                        onDuplicateAlgorithmRequested: {
                            console.log("QML SettingsView: Запрошено дублирование алгоритма ID:", algorithmId)
                            var newAlgorithmId = appData.duplicateAlgorithm(algorithmId)
                            if (typeof newAlgorithmId === 'number' && newAlgorithmId > 0) {
                                console.log("QML SettingsView: Алгоритм ID", algorithmId, "дублирован успешно. Новый ID:", newAlgorithmId)
                                // Перезагружаем список, чтобы увидеть новую копию
                                algorithmsListView.loadAlgorithms()
                            } else {
                                console.warn("QML SettingsView: Ошибка дублирования алгоритма ID", algorithmId, ". Результат:", newAlgorithmId)
                                // TODO: Отобразить ошибку пользователю
                            }
                        }
                        onEditActionsRequested: {
                            console.log("QML SettingsView: Запрошено редактирование действий для алгоритма:", JSON.stringify(algorithmData));
                            // Предполагается, что algorithmActionsDialog уже создан и доступен в этой области видимости
                            // как это сделано в предыдущем примере кода.
                            if (typeof algorithmActionsDialog !== 'undefined' && algorithmActionsDialog) {
                                algorithmActionsDialog.loadData(algorithmData);
                                algorithmActionsDialog.open();
                            } else {
                                console.error("QML SettingsView: ОШИБКА - algorithmActionsDialog не найден!");
                                // TODO: Открыть диалог каким-то другим способом или показать сообщение об ошибке
                            }
                        }
                    }
                    
                    // Диалог редактора алгоритма
                    AlgorithmEditorDialog {
                        id: algorithmEditorDialog
                        // Подключаемся к сигналу сохранения, чтобы обновить список
                        onAlgorithmSaved: {
                            console.log("QML SettingsView: Получен сигнал algorithmSaved от AlgorithmEditorDialog. Перезагружаем список.")
                            algorithmsListView.loadAlgorithms()
                            // Или можно обновить только конкретный элемент, если известен ID
                            // algorithmsListView.updateOrAddAlgorithm(...)
                        }
                    }
                    // Диалог для редактирования действий алгоритма
                    AlgorithmActionsDialog {
                        id: algorithmActionsDialog
                    }
                }
            }

            // --- Вкладка 4: Организации ---
            Item {
                id: organizationsTab
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 10

                    // --- Заголовок ---
                    Label {
                        text: "Справочник организаций"
                        font.pointSize: 14
                        font.bold: true
                    }

                    // --- Панель кнопок управления ---
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Rectangle {
                            Layout.preferredWidth: 110
                            Layout.preferredHeight: 36
                            radius: 8
                            color: {
                                if (addOrgBtn.pressed) return "#218c3d"
                                if (addOrgBtn.hovered) return "#2ecc71"
                                return "#27ae60"
                            }
                            Behavior on color { ColorAnimation { duration: 150 } }
                            MouseArea {
                                id: addOrgBtn
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    organizationEditorDialog.resetForAdd()
                                    organizationEditorDialog.open()
                                }
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "➕ Добавить"
                                color: "#ffffff"
                                font.pixelSize: 13
                                font.bold: true
                            }
                        }
                        Rectangle {
                            Layout.preferredWidth: 130
                            Layout.preferredHeight: 36
                            radius: 8
                            color: {
                                if (editOrgBtn.pressed) return "#c9951d"
                                if (editOrgBtn.hovered) return "#f39c12"
                                return "#f1c40f"
                            }
                            Behavior on color { ColorAnimation { duration: 150 } }
                            opacity: organizationsListView.currentIndex !== -1 ? 1.0 : 0.5
                            MouseArea {
                                id: editOrgBtn
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                enabled: organizationsListView.currentIndex !== -1
                                onClicked: {
                                    if (organizationsListView.currentIndex !== -1) {
                                        var orgData = organizationsListView.getOrganizationData(organizationsListView.currentIndex)
                                        organizationEditorDialog.loadDataForEdit(orgData)
                                        organizationEditorDialog.open()
                                    }
                                }
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "✏️ Редактировать"
                                color: "#2c3e50"
                                font.pixelSize: 13
                                font.bold: true
                            }
                        }
                        Rectangle {
                            Layout.preferredWidth: 110
                            Layout.preferredHeight: 36
                            radius: 8
                            color: {
                                if (delOrgBtn.pressed) return "#c0392b"
                                if (delOrgBtn.hovered) return "#e74c3c"
                                return "#e8453c"
                            }
                            Behavior on color { ColorAnimation { duration: 150 } }
                            opacity: organizationsListView.currentIndex !== -1 ? 1.0 : 0.5
                            MouseArea {
                                id: delOrgBtn
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                enabled: organizationsListView.currentIndex !== -1
                                onClicked: {
                                    if (organizationsListView.currentIndex !== -1) {
                                        var orgData = organizationsListView.getOrganizationData(organizationsListView.currentIndex)
                                        deleteConfirmationDialog.orgIdToDelete = orgData.id
                                        deleteConfirmationDialog.orgNameToDelete = orgData.name
                                        deleteConfirmationDialog.open()
                                    }
                                }
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "🗑️ Удалить"
                                color: "#ffffff"
                                font.pixelSize: 13
                                font.bold: true
                            }
                        }
                        Item { Layout.fillWidth: true }
                        Rectangle {
                            Layout.preferredWidth: 110
                            Layout.preferredHeight: 36
                            radius: 8
                            color: {
                                if (refreshOrgBtn.pressed) return "#2980b9"
                                if (refreshOrgBtn.hovered) return "#3498db"
                                return "#5dade2"
                            }
                            Behavior on color { ColorAnimation { duration: 150 } }
                            MouseArea {
                                id: refreshOrgBtn
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: organizationsListView.loadOrganizations()
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "🔄 Обновить"
                                color: "#ffffff"
                                font.pixelSize: 13
                                font.bold: true
                            }
                        }
                    }

                    // --- Список организаций ---
                    OrganizationsListView {
                        id: organizationsListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        onOrganizationDoubleClicked: {
                            var orgData = organizationsListView.getOrganizationData(organizationsListView.currentIndex)
                            if (orgData) {
                                organizationEditorDialog.loadDataForEdit(orgData)
                                organizationEditorDialog.open()
                            }
                        }
                    }
                }

                // --- Диалог редактирования организации ---
                OrganizationEditorDialog {
                    id: organizationEditorDialog
                    onOrganizationSaved: {
                        organizationsListView.loadOrganizations()
                    }
                }

                // --- Диалог подтверждения удаления ---
                Dialog {
                    id: deleteConfirmationDialog
                    title: "Подтверждение удаления"
                    standardButtons: Dialog.Yes | Dialog.No
                    modal: true
                    property int orgIdToDelete: -1
                    property string orgNameToDelete: ""

                    Label {
                        text: "Вы действительно хотите удалить организацию \"" + deleteConfirmationDialog.orgNameToDelete + "\"?"
                        wrapMode: Text.WordWrap
                    }

                    onAccepted: {
                        if (orgIdToDelete > 0) {
                            appData.deleteOrganization(orgIdToDelete)
                            organizationsListView.loadOrganizations()
                        }
                    }
                }
            }
        }
    }

    function saveSettings() {
        console.log("QML SettingsView: === НАЧАЛО СОХРАНЕНИЯ НАСТРОЕК ===");
        
        console.log("QML SettingsView: 1. Сбор настроек из полей ввода...");
        // --- СБОР НАСТРОЕК "ПОСТ" ---
        console.log("QML SettingsView: 2. Сбор настроек раздела 'Пост'...");
        var postSettings = {};
        postSettings['post_number'] = postNumberField.text.trim();
        postSettings['post_name'] = postNameField.text.trim();
        postSettings['workplace_name'] = workplaceNameField.text.trim();
        console.log("QML SettingsView: 2. Собраны настройки 'Пост':", JSON.stringify(postSettings));
        // --- ---

        // --- СБОР НАСТРОЕК "НАПОМИНАНИЙ И ЗВУКА" ---
        console.log("QML SettingsView: 3. Сбор настроек раздела 'Напоминания и звук'...");
        var reminderSoundSettings = {};
        // SQLite хранит BOOLEAN как 1/0
        reminderSoundSettings['use_persistent_reminders'] = persistentRemindersCheckBox.checked ? 1 : 0;
        reminderSoundSettings['sound_enabled'] = soundEnabledCheckBox.checked ? 1 : 0;
        console.log("QML SettingsView: 3. Собраны настройки 'Напоминания и звук':", JSON.stringify(reminderSoundSettings));
        // --- ---

        // --- СБОР НОВЫХ НАСТРОЕК ВРЕМЕНИ ---
        console.log("QML SettingsView: 4. Сбор настроек раздела 'Время'...");
        var timeSettings = {};
        timeSettings['custom_time_label'] = customTimeLabelField.text.trim();
        // Преобразуем часы из SpinBox в секунды для хранения в БД
        timeSettings['custom_time_offset_seconds'] = customTimeOffsetSpinBox.value * 3600;
        // SQLite хранит BOOLEAN как 1/0
        timeSettings['show_moscow_time'] = showMoscowTimeCheckBox.checked ? 1 : 0;
        // Преобразуем часы из SpinBox в секунды для хранения в БД
        timeSettings['moscow_time_offset_seconds'] = moscowTimeOffsetSpinBox.value * 3600;
        console.log("QML SettingsView: 4. Собраны настройки 'Время':", JSON.stringify(timeSettings));
        // --- ---

        // --- СБОР НАСТРОЕК "ВНЕШНЕГО ВИДА" ---
        console.log("QML SettingsView: 5. Сбор настроек раздела 'Внешний вид'...");
        var appearanceSettings = {};
        appearanceSettings['background_image_path'] = backgroundImagePathField.text.trim() || null; // Пустая строка -> NULL
        appearanceSettings['font_family'] = fontFamilyComboBox.currentText.trim() || "Arial"; // Значение по умолчанию
        appearanceSettings['font_size'] = fontSizeSpinBox.value;
        // Получаем значение 'value' из выбранного элемента модели
        if (fontStyleComboBox.currentIndex !== -1 && fontStyleComboBox.model.get(fontStyleComboBox.currentIndex)) {
            appearanceSettings['font_style'] = fontStyleComboBox.model.get(fontStyleComboBox.currentIndex).value;
        } else {
            appearanceSettings['font_style'] = "normal"; // Значение по умолчанию
        }
        appearanceSettings['background_color'] = backgroundColorField.text.trim() || "#ecf0f1"; // Значение по умолчанию
        console.log("QML SettingsView: 5. Собраны настройки 'Внешний вид':", JSON.stringify(appearanceSettings));
        // --- ---

        // --- СБОР НАСТРОЕК "ПЕЧАТИ" ---
        console.log("QML SettingsView: 6. Сбор настроек раздела 'Печать'...");
        var printSettings = {};
        // Пока используем те же значения, что и для интерфейса, или отдельные, если будут поля
        printSettings['print_font_family'] = fontFamilyComboBox.currentText.trim() || "Arial"; // Пока так
        printSettings['print_font_size'] = fontSizeSpinBox.value; // Пока так
        console.log("QML SettingsView: 6. Собраны настройки 'Печать':", JSON.stringify(printSettings));
        // --- ---

        // --- СБОР НАСТРОЕК "ШРИФТА ДЛЯ ПЕЧАТИ" ---
        console.log("QML SettingsView: 6. Сбор настроек раздела 'Шрифт для печати'...");
        var printSettings = {};
        printSettings['print_font_family'] = printFontFamilyComboBox.currentText.trim() || "Arial"; // Значение по умолчанию
        printSettings['print_font_size'] = printFontSizeSpinBox.value;
        // --- НОВОЕ: Сбор начертания шрифта для печати ---
        // Получаем значение 'value' из выбранного элемента модели
        if (printFontStyleComboBox.currentIndex !== -1 && printFontStyleComboBox.model.get(printFontStyleComboBox.currentIndex)) {
            printSettings['print_font_style'] = printFontStyleComboBox.model.get(printFontStyleComboBox.currentIndex).value;
        } else {
            printSettings['print_font_style'] = "normal"; // Значение по умолчанию
        }
        // --- ---
        console.log("QML SettingsView: 6. Собраны настройки 'Шрифт для печати':", JSON.stringify(printSettings));
        // --- ---

        // --- ОБЪЕДИНЕНИЕ ВСЕХ НАСТРОЕК В ОДИН СЛОВАРЬ ---
        console.log("QML SettingsView: 7. Объединение всех настроек в один словарь...");
        var allSettings = {};
        // Добавляем настройки "Пост"
        for (var key in postSettings) {
            if (postSettings.hasOwnProperty(key)) {
                allSettings[key] = postSettings[key];
            }
        }
        // Добавляем настройки "Напоминания и звук"
        for (var key_rs in reminderSoundSettings) {
            if (reminderSoundSettings.hasOwnProperty(key_rs)) {
                allSettings[key_rs] = reminderSoundSettings[key_rs];
            }
        }
        // Добавляем настройки "Время"
        for (var key_t in timeSettings) {
            if (timeSettings.hasOwnProperty(key_t)) {
                allSettings[key_t] = timeSettings[key_t];
            }
        }
        // Добавляем настройки "Внешнего вида"
        for (var key_a in appearanceSettings) {
            if (appearanceSettings.hasOwnProperty(key_a)) {
                allSettings[key_a] = appearanceSettings[key_a];
            }
        }
        // Добавляем настройки "Печати"
        for (var key_p in printSettings) {
            if (printSettings.hasOwnProperty(key_p)) {
                allSettings[key_p] = printSettings[key_p];
            }
        }
        console.log("QML SettingsView: 7. Все настройки объединены. Отправляемый словарь:", JSON.stringify(allSettings).substring(0, 500));
        // --- ---

        console.log("QML SettingsView: 8. Отправка настроек в Python для сохранения...");
        var result = appData.updateSettings(allSettings);
        console.log("QML SettingsView: 9. Получен результат сохранения из Python:", result);

        if (result === true) {
            console.log("QML SettingsView: === НАСТРОЙКИ УСПЕШНО СОХРАНЕНЫ ===");
            showSuccessMessage("Настройки сохранены успешно");
            // --- НОВОЕ: Уведомляем об изменении внешнего вида ---
            // appData.appearanceSettingsChanged.emit(); // Если такой сигнал будет добавлен
            // --- ---
        } else {
            var errorMsgSave = "Неизвестная ошибка";
            if (typeof result === 'string') {
                errorMsgSave = result;
            } else if (result === false) {
                errorMsgSave = "Не удалось выполнить операцию. Проверьте данные.";
            } else if (result === -1) {
                errorMsgSave = "Ошибка при сохранении настроек.";
            }
            console.error("QML SettingsView: === ОШИБКА СОХРАНЕНИЯ НАСТРОЕК ===", errorMsgSave);
            showErrorMessage("Ошибка сохранения настроек: " + errorMsgSave);
        }
        console.log("QML SettingsView: === КОНЕЦ СОХРАНЕНИЯ НАСТРОЕК ===");
    }

    function loadSettings() {
        console.log("QML SettingsView: === НАЧАЛО ЗАГРУЗКИ НАСТРОЕК ===");
        console.log("QML SettingsView: 1. Запрос полных настроек у Python...");
        var settings = appData.getFullSettings();
        console.log("QML SettingsView: 2. Полученные настройки (сырой):", JSON.stringify(settings).substring(0, 500));

        // --- Преобразование QJSValue/QVariant в словарь JS ---
        console.log("QML SettingsView: 3. Проверка необходимости преобразования QJSValue...");
        if (settings && typeof settings === 'object' && typeof settings.hasOwnProperty === 'function' && settings.hasOwnProperty('toVariant')) {
            console.log("QML SettingsView: 3a. Обнаружен QJSValue, преобразование в QVariant/JS...");
            settings = settings.toVariant();
            console.log("QML SettingsView: 3b. QJSValue (settings) преобразован в:", JSON.stringify(settings).substring(0, 500));
        } else {
            console.log("QML SettingsView: 3a. Преобразование не требуется или невозможно.");
        }
        // --- ---

        if (settings && typeof settings === 'object') {
            console.log("QML SettingsView: 4. Настройки получены в виде объекта. Начало заполнения полей ввода...");
            
            // --- ЗАГРУЗКА НАСТРОЕК "ПОСТ" ---
            console.log("QML SettingsView: 5. Загрузка настроек раздела 'Пост'...");
            // Номер поста
            if (settings.post_number !== undefined) {
                postNumberField.text = String(settings.post_number);
                console.log("QML SettingsView: 5a. Загружен post_number:", postNumberField.text);
            }
            // Название поста
            if (settings.post_name !== undefined) {
                postNameField.text = String(settings.post_name);
                console.log("QML SettingsView: 5b. Загружен post_name:", postNameField.text);
            }
            // Название рабочего места
            if (settings.workplace_name !== undefined) {
                workplaceNameField.text = String(settings.workplace_name);
                console.log("QML SettingsView: 5c. Загружено workplace_name:", workplaceNameField.text);
            }
            console.log("QML SettingsView: 5. Загрузка настроек раздела 'Пост' завершена.");
            // --- ---

            // --- ЗАГРУЗКА НАСТРОЕК "НАПОМИНАНИЙ И ЗВУКА" ---
            console.log("QML SettingsView: 6. Загрузка настроек раздела 'Напоминания и звук'...");
            // Настойчивые напоминания
            if (settings.use_persistent_reminders !== undefined) {
                // Преобразуем 1/0 из SQLite в true/false для QML CheckBox
                persistentRemindersCheckBox.checked = (settings.use_persistent_reminders === 1 || settings.use_persistent_reminders === true);
                console.log("QML SettingsView: 6a. Загружено use_persistent_reminders:", persistentRemindersCheckBox.checked);
            }
            // Звук
            if (settings.sound_enabled !== undefined) {
                // Преобразуем 1/0 из SQLite в true/false для QML CheckBox
                soundEnabledCheckBox.checked = (settings.sound_enabled === 1 || settings.sound_enabled === true);
                console.log("QML SettingsView: 6b. Загружено sound_enabled:", soundEnabledCheckBox.checked);
            }
            console.log("QML SettingsView: 6. Загрузка настроек раздела 'Напоминания и звук' завершена.");
            // --- ---

            // --- ЗАГРУЗКА НОВЫХ НАСТРОЕК ВРЕМЕНИ ---
            console.log("QML SettingsView: 7. Загрузка настроек раздела 'Время'...");
            // Название местного времени
            if (settings.custom_time_label !== undefined) {
                customTimeLabelField.text = String(settings.custom_time_label);
                console.log("QML SettingsView: 7a. Загружено custom_time_label:", customTimeLabelField.text);
            }
            // Смещение местного времени (секунды -> часы для SpinBox)
            if (settings.custom_time_offset_seconds !== undefined) {
                var offsetSecs = parseInt(settings.custom_time_offset_seconds);
                if (!isNaN(offsetSecs)) {
                    var offsetHours = Math.floor(offsetSecs / 3600);
                    customTimeOffsetSpinBox.value = offsetHours;
                    console.log("QML SettingsView: 7b. Загружено custom_time_offset_seconds:", offsetSecs, "->", offsetHours, "ч");
                } else {
                    console.warn("QML SettingsView: 7b. Ошибка преобразования custom_time_offset_seconds:", settings.custom_time_offset_seconds);
                }
            }
            // Показывать московское время
            if (settings.show_moscow_time !== undefined) {
                // Преобразуем 1/0 из SQLite в true/false для QML CheckBox
                showMoscowTimeCheckBox.checked = (settings.show_moscow_time === 1 || settings.show_moscow_time === true);
                console.log("QML SettingsView: 7c. Загружено show_moscow_time:", showMoscowTimeCheckBox.checked);
            }
            // Смещение московского времени (секунды -> часы для SpinBox)
            if (settings.moscow_time_offset_seconds !== undefined) {
                var moscowOffsetSecs = parseInt(settings.moscow_time_offset_seconds);
                if (!isNaN(moscowOffsetSecs)) {
                    var moscowOffsetHours = Math.floor(moscowOffsetSecs / 3600);
                    moscowTimeOffsetSpinBox.value = moscowOffsetHours;
                    console.log("QML SettingsView: 7d. Загружено moscow_time_offset_seconds:", moscowOffsetSecs, "->", moscowOffsetHours, "ч");
                } else {
                    console.warn("QML SettingsView: 7d. Ошибка преобразования moscow_time_offset_seconds:", settings.moscow_time_offset_seconds);
                }
            }
            console.log("QML SettingsView: 7. Загрузка настроек раздела 'Время' завершена.");
            // --- ---

            // --- ЗАГРУЗКА НАСТРОЕК "ВНЕШНЕГО ВИДА" ---
            console.log("QML SettingsView: 8. Загрузка настроек раздела 'Внешний вид'...");
            // Путь к фоновому изображению/эмблеме
            if (settings.background_image_path !== undefined) {
                backgroundImagePathField.text = String(settings.background_image_path);
                console.log("QML SettingsView: 8a. Загружен background_image_path:", backgroundImagePathField.text);
            }
            // Шрифт интерфейса
            if (settings.font_family !== undefined) {
                var fontFamily = String(settings.font_family);
                // Проверяем, есть ли такой шрифт в комбо-боксе
                var fontFamilyIndex = fontFamilyComboBox.find(fontFamily);
                if (fontFamilyIndex !== -1) {
                    fontFamilyComboBox.currentIndex = fontFamilyIndex;
                } else {
                    // Если шрифт не найден, добавляем его в список (на случай кастомных шрифтов)
                    fontFamilyComboBox.model.append({"text": fontFamily});
                    fontFamilyComboBox.currentIndex = fontFamilyComboBox.count - 1;
                }
                console.log("QML SettingsView: 8b. Загружен font_family:", fontFamily);
            }
            // Размер шрифта интерфейса
            if (settings.font_size !== undefined) {
                var fontSize = parseInt(settings.font_size);
                if (!isNaN(fontSize) && fontSize >= fontSizeSpinBox.from && fontSize <= fontSizeSpinBox.to) {
                    fontSizeSpinBox.value = fontSize;
                } else {
                    fontSizeSpinBox.value = 12; // Значение по умолчанию
                }
                console.log("QML SettingsView: 8c. Загружен font_size:", fontSize);
            }
            // Начертание шрифта интерфейса
            if (settings.font_style !== undefined) {
                var fontStyle = String(settings.font_style);
                // Ищем значение в модели комбо-бокса
                for (var i = 0; i < fontStyleComboBox.model.count; i++) {
                    if (fontStyleComboBox.model.get(i).value === fontStyle) {
                        fontStyleComboBox.currentIndex = i;
                        break;
                    }
                }
                console.log("QML SettingsView: 8d. Загружено font_style:", fontStyle);
            }
            // Цвет фона
            if (settings.background_color !== undefined) {
                backgroundColorField.text = String(settings.background_color);
                console.log("QML SettingsView: 8e. Загружен background_color:", backgroundColorField.text);
            }
            console.log("QML SettingsView: 8. Загрузка настроек раздела 'Внешний вид' завершена.");
            // --- ---

            // --- ЗАГРУЗКА НАСТРОЕК "ПЕЧАТИ" ---
            console.log("QML SettingsView: 9. Загрузка настроек раздела 'Печать'...");
            // Шрифт для печати
            if (settings.print_font_family !== undefined) {
                var printFontFamily = String(settings.print_font_family);
                // Проверяем, есть ли такой шрифт в комбо-боксе для печати (если будет отдельный)
                // Пока используем тот же комбо-бокс, что и для интерфейса, или создаем отдельный
                // Для простоты, пока используем общий (но в будущем может понадобиться отдельный)
                // printFontFamilyComboBox.currentIndex = printFontFamilyComboBox.find(printFontFamily);
                console.log("QML SettingsView: 9a. Загружен print_font_family:", printFontFamily);
            }
            // Размер шрифта для печати
            if (settings.print_font_size !== undefined) {
                var printFontSize = parseInt(settings.print_font_size);
                if (!isNaN(printFontSize)) {
                    // printFontSizeSpinBox.value = printFontSize; // Если будет отдельный SpinBox
                    console.log("QML SettingsView: 9b. Загружен print_font_size:", printFontSize);
                }
            }
            console.log("QML SettingsView: 9. Загрузка настроек раздела 'Печать' завершена.");

            // --- ЗАГРУЗКА НАСТРОЕК "ШРИФТА ДЛЯ ПЕЧАТИ" ---
            console.log("QML SettingsView: 9. Загрузка настроек раздела 'Шрифт для печати'...");
            // Шрифт для печати
            if (settings.print_font_family !== undefined) {
                var printFontFamily = String(settings.print_font_family);
                // Проверяем, есть ли такой шрифт в комбо-боксе
                var printFontFamilyIndex = printFontFamilyComboBox.find(printFontFamily);
                if (printFontFamilyIndex !== -1) {
                    printFontFamilyComboBox.currentIndex = printFontFamilyIndex;
                } else {
                    // Если шрифт не найден, добавляем его в список (на случай кастомных шрифтов)
                    printFontFamilyComboBox.model.append(printFontFamily);
                    printFontFamilyComboBox.currentIndex = printFontFamilyComboBox.count - 1;
                }
                console.log("QML SettingsView: 9a. Загружен print_font_family:", printFontFamily);
            }
            // Размер шрифта для печати
            if (settings.print_font_size !== undefined) {
                var printFontSize = parseInt(settings.print_font_size);
                if (!isNaN(printFontSize) && printFontSize >= printFontSizeSpinBox.from && printFontSize <= printFontSizeSpinBox.to) {
                    printFontSizeSpinBox.value = printFontSize;
                } else {
                    printFontSizeSpinBox.value = 12; // Значение по умолчанию
                }
                console.log("QML SettingsView: 9b. Загружен print_font_size:", printFontSize);
            }
            // --- НОВОЕ: Начертание шрифта для печати ---
            if (settings.print_font_style !== undefined) {
                var printFontStyle = String(settings.print_font_style);
                // Ищем значение в модели комбо-бокса начертания
                var foundPrintFontStyleIndex = -1;
                for (var i_pfs = 0; i_pfs < printFontStyleComboBox.model.count; i_pfs++) {
                    // Проверяем свойство 'value' каждого элемента модели
                    if (printFontStyleComboBox.model.get(i_pfs).value === printFontStyle) {
                        foundPrintFontStyleIndex = i_pfs;
                        break;
                    }
                }
                if (foundPrintFontStyleIndex !== -1) {
                    printFontStyleComboBox.currentIndex = foundPrintFontStyleIndex;
                } else {
                    // Если стиль не найден, устанавливаем "Обычный" (индекс 0 в стандартной модели)
                    printFontStyleComboBox.currentIndex = 0;
                }
                console.log("QML SettingsView: 9c. Загружено print_font_style:", printFontStyle, "Индекс:", foundPrintFontStyleIndex);
            }
            // --- ---
            console.log("QML SettingsView: 9. Загрузка настроек раздела 'Шрифт для печати' завершена.");
            // --- ---


            console.log("QML SettingsView: === КОНЕЦ ЗАГРУЗКИ НАСТРОЕК ===");
        } else {
            console.log("QML SettingsView: Не удалось загрузить настройки или они пусты");
        }
    }

    // --- Функция для загрузки списка из Python ---
    function loadDutyOfficers() {
        console.log("QML SettingsView: Запрос списка должностных лиц у Python...");
        // Вызываем слот Python, который возвращает список
        var officersList = appData.getDutyOfficersList(); // <-- Получаем список
        console.log("QML SettingsView: Получен список из Python (сырой):", JSON.stringify(officersList));

        // --- НОВОЕ: Преобразование QJSValue/QVariant в массив JS ---
        // Если officersList - это QJSValue (из Python), преобразуем его
        if (officersList && typeof officersList === 'object' && officersList.hasOwnProperty('toVariant')) {
            officersList = officersList.toVariant();
            console.log("QML SettingsView: QJSValue (officersList) преобразован в:", JSON.stringify(officersList));
        }
        // --- ---

        // Очищаем текущую модель
        officersListModel.clear();
        console.log("QML SettingsView: Модель ListView очищена.");

        // --- ИЗМЕНЕНО: Более гибкая проверка на "массивоподобность" ---
        // Вместо Array.isArray, проверяем, есть ли у объекта свойство length (не undefined)
        // Это работает как для JS Array, так и для QVariantList, переданного из Python
        if (officersList && typeof officersList === 'object' && officersList.length !== undefined) {
        // --- ---
            var count = officersList.length;
            console.log("QML SettingsView: Полученный список является массивоподобным. Количество элементов:", count);
            // Заполняем модель данными по одному
            for (var i = 0; i < count; i++) {
                var officer = officersList[i];
                console.log("QML SettingsView: Обрабатываем элемент", i, ":", JSON.stringify(officer)); // Лог каждого элемента
                // Убедимся, что элемент - это объект
                if (typeof officer === 'object' && officer !== null) {
                    // --- ИЗМЕНЕНО: Явное копирование свойств ---
                    // Вместо officersListModel.append(officer), создаем новый JS объект
                    // Это помогает избежать проблем с QJSValue/QVariantMap, которые могут
                    // не сериализоваться корректно внутри ListModel.
                    var officerCopy = ({
                        "id": officer["id"],
                        "rank": officer["rank"],
                        "last_name": officer["last_name"],
                        "first_name": officer["first_name"],
                        "middle_name": officer["middle_name"],
                        "phone": officer["phone"], // Предполагаем, что phone тоже передается
                        "is_active": officer["is_active"], // Предполагаем, что is_active тоже передается
                        "is_admin": officer["is_admin"],
                        "login": officer["login"] // <-- Добавлено
                        // Добавьте другие поля, если они нужны для отображения в списке
                    });
                    // --- ---
                    try {
                        officersListModel.append(officerCopy); // <-- Добавляем КОПИЮ
                        console.log("QML SettingsView: Элемент", i, "добавлен в модель.");
                    } catch (e) {
                        console.error("QML SettingsView: Ошибка при добавлении элемента", i, "в модель:", e.toString(), "Данные:", JSON.stringify(officerCopy));
                    }
                } else {
                    console.warn("QML SettingsView: Элемент", i, "не является корректным объектом:", typeof officer, officer);
                }
            }
        } else {
            // --- ИЗМЕНЕНО: Сообщение об ошибке ---
            console.error("QML SettingsView: Python не вернул корректный массивоподобный объект. Получен тип:", typeof officersList, "Значение:", officersList);
            // --- ---
        }
        console.log("QML SettingsView: Модель ListView обновлена. Элементов:", officersListModel.count);
        // --- ДОБАВЛЕНО: Отладка содержимого модели ---
        if (officersListModel.count > 0) {
             try {
                 console.log("QML SettingsView: Первый элемент в модели (попытка):", JSON.stringify(officersListModel.get(0)));
             } catch (e_get) {
                 console.warn("QML SettingsView: Не удалось сериализовать первый элемент модели для лога:", e_get.toString());
                 // Попробуем получить отдельные свойства
                 var firstItem = officersListModel.get(0);
                 if (firstItem) {
                     console.log("QML SettingsView: Первый элемент в модели (свойства): id=", firstItem.id, "rank=", firstItem.rank, "last_name=", firstItem.last_name);
                 }
             }
        }
        // --- ---
    }
    // --- ---

    // --- Отслеживание активации вкладки "Должностные лица" ---
    Connections {
        target: settingsTabBar
        function onCurrentIndexChanged() {
            // Проверяем, является ли активной вкладка "Должностные лица"
            // Индекс вкладки "Должностные лица" - 1 (вторая вкладка, индекс с 0)
            if (settingsTabBar.currentIndex === 1) {
                console.log("QML SettingsView: Вкладка 'Должностные лица' активирована. Загрузка списка...");
                loadDutyOfficers(); // Загружаем список при активации вкладки
            }
            // Индекс вкладки "Алгоритмы" - 2 (третья вкладка, индекс с 0)
            if (settingsTabBar.currentIndex === 2) {
                console.log("QML SettingsView: Вкладка 'Алгоритмы' активирована. Загрузка списка...");
                // Проверяем, существует ли функция, и вызываем её
                // algorithmsListView - это id компонента AlgorithmsListView в algorithmsTab
                if (algorithmsListView && typeof algorithmsListView.loadAlgorithms === 'function') {
                    algorithmsListView.loadAlgorithms();
                } else {
                    console.error("QML SettingsView: ОШИБКА - algorithmsListView или algorithmsListView.loadAlgorithms не найдены!");
                }
            }
        }
    }
    // --- Автоматическая загрузка при открытии SettingsView ---
    Component.onCompleted: {
        // Этот код выполнится, когда компонент SettingsView будет полностью создан
        console.log("QML SettingsView: Загружен. Инициализация...");
        loadSettings();
    }
}