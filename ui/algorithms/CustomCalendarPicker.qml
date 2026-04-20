// ui/algorithms/CustomCalendarPicker.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Popup {
    id: customCalendarPicker

    // --- Свойства ---
    property date selectedDate: new Date() // Текущая дату по умолчанию
    property string selectedDateString: Qt.formatDate(selectedDate, "dd.MM.yyyy") // Форматированная строка даты
    signal dateSelected(date selectedDate)
    // --- ---

    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    width: Math.min(parent.width * 0.8, 350)
    height: Math.min(parent.height * 0.8, 400)
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    background: Rectangle {
        color: "white"
        border.color: "lightgray"
        radius: 5
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        // --- Заголовок с навигацией ---
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 5

            // Навигация: Месяц и год
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Button {
                    text: "◀"
                    onClicked: {
                        console.log("QML CustomCalendarPicker: Нажата кнопка 'Предыдущий месяц'.");
                        // Перейти к предыдущему месяцу
                        var newDate = new Date(customCalendarPicker.selectedDate);
                        newDate.setMonth(newDate.getMonth() - 1);
                        customCalendarPicker.selectedDate = newDate;
                        console.log("QML CustomCalendarPicker: Предыдущий месяц. Новая дата:", Qt.formatDate(customCalendarPicker.selectedDate, "yyyy-MM-dd"));
                    }
                }

                // Отображение названия месяца и года
                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    // --- ИЗМЕНЕНО: Отображаем только название месяца ---
                    text: Qt.locale().monthName(customCalendarPicker.selectedDate.getMonth())
                    // --- ---
                    font.bold: true
                }

                Button {
                    text: "▶"
                    onClicked: {
                        console.log("QML CustomCalendarPicker: Нажата кнопка 'Следующий месяц'.");
                        // Перейти к следующему месяцу
                        var newDate = new Date(customCalendarPicker.selectedDate);
                        newDate.setMonth(newDate.getMonth() + 1);
                        customCalendarPicker.selectedDate = newDate;
                        console.log("QML CustomCalendarPicker: Следующий месяц. Новая дата:", Qt.formatDate(customCalendarPicker.selectedDate, "yyyy-MM-dd"));
                    }
                }
            }

            // Выбор года
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Label {
                    text: "Год:"
                }

                // SpinBox для выбора года
                // Ограничиваем разумным диапазоном, например, 1900-2100
                SpinBox {
                    id: yearSpinBox
                    Layout.fillWidth: true
                    from: 1900
                    to: 2100
                    stepSize: 1
                    // --- ИЗМЕНЕНО: Устанавливаем начальное значение ---
                    // value будет установлен в onSelectedDateChanged и onCompleted
                    // --- ---
                    // Обработчик изменения значения
                    onValueChanged: {
                        console.log("QML CustomCalendarPicker: SpinBox год изменился на:", value);
                        // Проверяем, изменился ли год относительно selectedDate
                        // Это важно, чтобы избежать бесконечных циклов обновлений
                        if (value !== customCalendarPicker.selectedDate.getFullYear()) {
                            console.log("QML CustomCalendarPicker: Год в SpinBox отличается от года в selectedDate. Обновляем selectedDate.");
                            var newDate = new Date(customCalendarPicker.selectedDate);
                            newDate.setFullYear(value);
                            // Проверка на корректность даты (например, 29 февраля в невисокосном году)
                            if (newDate.getMonth() !== customCalendarPicker.selectedDate.getMonth()) {
                                // Это произошло, если день был 29/30/31, а новый месяц короче
                                // Например, 31.03.2023 -> 31.02.2023 -> 03.03.2023
                                // В этом случае setDate "перескочит" на следующий месяц
                                // Мы можем либо принять это поведение, либо скорректировать день
                                // до последнего дня нового месяца.
                                // Для простоты, примем поведение JS Date.
                                console.log("QML CustomCalendarPicker: День был скорректирован JS Date при смене года:", Qt.formatDate(customCalendarPicker.selectedDate, "yyyy-MM-dd"), "->", Qt.formatDate(newDate, "yyyy-MM-dd"));
                            }
                            customCalendarPicker.selectedDate = newDate;
                        } else {
                            console.log("QML CustomCalendarPicker: Год в SpinBox совпадает с годом в selectedDate. Обновление не требуется.");
                        }
                    }
                }
            }
        }
        // --- ---

        // --- Заголовки дней недели ---
        RowLayout {
            Layout.fillWidth: true
            spacing: 5
            Repeater {
                model: 7
                delegate: Rectangle {
                    Layout.fillWidth: true
                    height: 30
                    color: "#ecf0f1"
                    border.color: "#bdc3c7"
                    Text {
                        anchors.centerIn: parent
                        // --- ИСПРАВЛЕНО: Начинаем с Понедельника БЕЗ объявления var ---
                        // Qt.locale().dayName(0) = Вс.
                        // Qt.locale().dayName(1) = Пн.
                        // Нам нужно, чтобы index=0 в Repeater соответствовал Пн.
                        // Используем (index + 1) % 7. При index=0 -> dayIndex=1 (Пн). При index=6 -> dayIndex=0 (Вс).
                        // text: Qt.locale().dayName((index + 1) % 7, Locale.ShortFormat) // <-- Вариант 1: Простое выражение
                        // Или, для лучшей читаемости, используем IIFE:
                        text: (function() {
                            var dayIndex = (index + 1) % 7;
                            return Qt.locale().dayName(dayIndex, Locale.ShortFormat);
                        })()
                        // --- ---
                        font.pixelSize: 10
                        font.bold: true
                    }
                }
            }
        }
        // --- ---

        // --- Сетка дней месяца ---
        GridView {
            id: daysGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            cellWidth: width / 7
            cellHeight: (height - 10) / 6 // Примерно 6 строк
            model: ListModel { id: daysModel }
            delegate: Rectangle {
                width: daysGrid.cellWidth
                height: daysGrid.cellHeight
                color: {
                    if (model.isCurrentMonth) {
                        if (model.isSelected) {
                            return "#3498db"; // Выбранный день
                        } else if (model.isToday) {
                            return "#2ecc71"; // Сегодня
                        } else {
                            return index % 2 ? "#f9f9f9" : "#ffffff"; // Обычные дни
                        }
                    } else {
                        return "#ecf0f1"; // Дни пред/след месяца
                    }
                }
                border.color: model.isCurrentMonth ? "#ddd" : "#bdc3c7"
                Text {
                    anchors.centerIn: parent
                    text: model.dayNumber
                    color: model.isCurrentMonth ? (model.isSelected || model.isToday ? "white" : "black") : "#95a5a6"
                    font.pixelSize: 10
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (model.isCurrentMonth) {
                            console.log("QML CustomCalendarPicker: Выбран день:", model.fullDateString);
                            // Создаем объект Date из строки
                            var chosenDate = new Date(model.fullDateString + "T00:00:00"); // Используем ISO формат для избежания проблем с TZ
                            customCalendarPicker.selectedDate = chosenDate;
                            customCalendarPicker.dateSelected(chosenDate);
                            customCalendarPicker.close();
                        }
                    }
                }
            }
        }
        // --- ---

        // --- Кнопки ---
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Item { Layout.fillWidth: true } // Заполнитель
            Button {
                text: "Отмена"
                onClicked: customCalendarPicker.close()
            }
            Button {
                text: "ОК"
                onClicked: {
                    console.log("QML CustomCalendarPicker: OK. Выбранная дата:", Qt.formatDate(customCalendarPicker.selectedDate, "yyyy-MM-dd"));
                    customCalendarPicker.dateSelected(customCalendarPicker.selectedDate);
                    customCalendarPicker.close();
                }
            }
        }
        // --- ---
    }

    // --- Обновление модели дней при изменении selectedDate ---
    onSelectedDateChanged: {
        console.log("QML CustomCalendarPicker: selectedDate changed to:", Qt.formatDate(selectedDate, "yyyy-MM-dd"));
        updateDaysModel();
        customCalendarPicker.selectedDateString = Qt.formatDate(selectedDate, "dd.MM.yyyy");
        // --- НОВОЕ: Обновляем значение SpinBox с годом ---
        // Устанавливаем значение только если оно отличается, чтобы избежать лишних сигналов
        if (yearSpinBox.value !== selectedDate.getFullYear()) {
            console.log("QML CustomCalendarPicker: Обновление yearSpinBox.value на:", selectedDate.getFullYear());
            yearSpinBox.value = selectedDate.getFullYear();
        } else {
            console.log("QML CustomCalendarPicker: yearSpinBox.value уже равен году в selectedDate. Обновление не требуется.");
        }
        // --- ---
    }

    Component.onCompleted: {
        console.log("QML CustomCalendarPicker: Загружен. Инициализация...");
        updateDaysModel();
        // --- НОВОЕ: Устанавливаем начальное значение для yearSpinBox ---
        console.log("QML CustomCalendarPicker: Установка начального значения yearSpinBox на:", selectedDate.getFullYear());
        yearSpinBox.value = selectedDate.getFullYear(); // Это также вызовет onValueChanged, но логика внутри него это учтет
        // --- ---
    }

    /**
     * Обновляет модель дней (daysModel) для отображения в GridView
     */
    function updateDaysModel() {
        console.log("QML CustomCalendarPicker: Обновление модели дней для даты:", Qt.formatDate(selectedDate, "yyyy-MM-dd"));
        daysModel.clear();

        var currentDate = new Date(selectedDate); // Работаем с копией
        var year = currentDate.getFullYear();
        var month = currentDate.getMonth(); // 0-11

        // Первый день месяца
        var firstDayOfMonth = new Date(year, month, 1);
        // День недели первого дня месяца (0 - Воскресенье, 6 - Суббота)
        var firstDayWeekday = firstDayOfMonth.getDay();
        // Корректируем: 0 (Вс) -> 6, 1 (Пн) -> 0, ..., 6 (Сб) -> 5
        // Или используем стандарт: 0 (Пн) -> 0, ..., 6 (Вс) -> 6. Qt.locale().firstDayOfWeek может помочь.
        // Для простоты, будем считать, что неделя начинается с Понедельника (1 в Qt, 1 в JS Date)
        var startDayOffset = (firstDayWeekday + 6) % 7; // Сдвиг до первого понедельника

        // Последний день месяца
        var lastDayOfMonth = new Date(year, month + 1, 0);
        var daysInMonth = lastDayOfMonth.getDate();

        // Дата сегодня
        var today = new Date();
        var todayString = Qt.formatDate(today, "yyyy-MM-dd");

        // Предыдущий месяц
        var prevMonthLastDay = new Date(year, month, 0).getDate();

        // Сначала добавляем дни предыдущего месяца
        for (var i = 0; i < startDayOffset; i++) {
            var dayNumber = prevMonthLastDay - startDayOffset + i + 1;
            var dayDate = new Date(year, month - 1, dayNumber);
            var dayDateString = Qt.formatDate(dayDate, "yyyy-MM-dd");
            daysModel.append({
                "dayNumber": dayNumber,
                "isCurrentMonth": false,
                "isToday": dayDateString === todayString,
                "isSelected": false, // Не может быть выбран, так как не текущий месяц
                "fullDateString": dayDateString
            });
        }

        // Затем дни текущего месяца
        for (var day = 1; day <= daysInMonth; day++) {
            var dayDateCurrent = new Date(year, month, day);
            var dayDateStringCurrent = Qt.formatDate(dayDateCurrent, "yyyy-MM-dd");
            daysModel.append({
                "dayNumber": day,
                "isCurrentMonth": true,
                "isToday": dayDateStringCurrent === todayString,
                "isSelected": Qt.formatDate(dayDateCurrent, "yyyy-MM-dd") === Qt.formatDate(selectedDate, "yyyy-MM-dd"),
                "fullDateString": dayDateStringCurrent
            });
        }

        // Кол-во ячеек в сетке (6 строк * 7 дней = 42)
        var totalCellsNeeded = 42;
        var daysAddedSoFar = startDayOffset + daysInMonth;
        var nextMonthDay = 1;

        // Добавляем дни следующего месяца, чтобы заполнить сетку
        while (daysAddedSoFar < totalCellsNeeded) {
            var dayDateNext = new Date(year, month + 1, nextMonthDay);
            var dayDateStringNext = Qt.formatDate(dayDateNext, "yyyy-MM-dd");
            daysModel.append({
                "dayNumber": nextMonthDay,
                "isCurrentMonth": false,
                "isToday": dayDateStringNext === todayString,
                "isSelected": false, // Не может быть выбран, так как не текущий месяц
                "fullDateString": dayDateStringNext
            });
            nextMonthDay++;
            daysAddedSoFar++;
        }

        console.log("QML CustomCalendarPicker: Модель дней обновлена. Всего дней:", daysModel.count);
    }
    // --- ---
}