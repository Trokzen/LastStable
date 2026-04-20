// ui/algorithms/CalendarView.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Item {
    id: calendarViewRoot

    // --- Свойства ---
    property date selectedDate: new Date() // Текущая дата по умолчанию
    property string selectedDateString: Qt.formatDate(selectedDate, "dd.MM.yyyy") // Форматированная строка даты
    // --- ---

    // --- Сигналы ---
    signal dateSelected(date selectedDate)
    signal executionSelected(var executionData) // Для передачи данных выбранного execution'а
    // --- ---

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        Label {
            text: "Выбор даты для просмотра истории алгоритмов"
            font.pointSize: 14
            font.bold: true
        }

        // --- Календарь ---
        Calendar {
            id: calendar
            Layout.fillWidth: true
            Layout.preferredHeight: 300 // Фиксированная высота для календаря
            // --- Привязка к выбранной дате ---
            onSelectedDateChanged: {
                console.log("QML CalendarView: Выбрана дата в календаре:", Qt.formatDate(calendar.selectedDate, "yyyy-MM-dd"));
                calendarViewRoot.selectedDate = calendar.selectedDate;
                calendarViewRoot.selectedDateString = Qt.formatDate(calendar.selectedDate, "dd.MM.yyyy");
                // Загружаем список execution'ов для выбранной даты
                calendarViewRoot.loadExecutionsForDate(Qt.formatDate(calendar.selectedDate, "yyyy-MM-dd"));
            }
            // --- ---
        }
        // --- ---

        // --- Выбранная дата ---
        Label {
            text: "Выбранная дата: " + calendarViewRoot.selectedDateString
            font.pointSize: 12
            font.bold: true
        }
        // --- ---

        // --- Список выполненных алгоритмов за выбранную дату ---
        GroupBox {
            title: "Выполненные алгоритмы за " + calendarViewRoot.selectedDateString
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                anchors.fill: parent
                spacing: 10

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    
                    ListView {
                        id: executionsListView
                        model: ListModel {
                            id: executionsModel
                        }
                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 60
                            color: index % 2 ? "#f9f9f9" : "#ffffff"
                            border.color: executionsListView.currentIndex === index ? "#3498db" : "#ddd"
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 5
                                spacing: 2

                                Text {
                                    Layout.fillWidth: true
                                    text: model.algorithm_name || "Без названия"
                                    font.bold: true
                                    elide: Text.ElideRight
                                }
                                RowLayout {
                                    Text {
                                        text: "Начало: " + (model.started_at_display || "")
                                        color: "gray"
                                        font.pixelSize: 10
                                    }
                                    Item {
                                        Layout.fillWidth: true
                                    }
                                    Text {
                                        text: "Ответственный: " + (model.created_by_user_display_name || "Неизвестен")
                                        color: "gray"
                                        font.pixelSize: 10
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    executionsListView.currentIndex = index;
                                    // Передаем копию данных execution'а
                                    calendarViewRoot.executionSelected({
                                        "id": model.id,
                                        "algorithm_id": model.algorithm_id,
                                        "algorithm_name": model.algorithm_name,
                                        "started_at": model.started_at,
                                        "started_at_display": model.started_at_display,
                                        "completed_at": model.completed_at,
                                        "completed_at_display": model.completed_at_display,
                                        "status": model.status,
                                        "created_by_user_id": model.created_by_user_id,
                                        "created_by_user_display_name": model.created_by_user_display_name
                                        // Добавьте другие поля, если они нужны
                                    });
                                }
                                onDoubleClicked: {
                                    executionsListView.currentIndex = index;
                                    var executionData = executionsModel.get(index);
                                    // TODO: Открыть детали execution'а
                                    console.log("QML CalendarView: Запрошено открытие деталей execution'а ID", executionData.id);
                                }
                            }
                        }
                    }
                }
                
                // --- Панель кнопок для execution'ов ---
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    enabled: executionsListView.currentIndex !== -1
                    
                    Button {
                        text: "Открыть детали"
                        onClicked: {
                            var index = executionsListView.currentIndex;
                            if (index !== -1) {
                                var executionData = executionsModel.get(index);
                                // TODO: Открыть детали execution'а
                                console.log("QML CalendarView: Запрошено открытие деталей execution'а ID", executionData.id);
                            }
                        }
                    }
                    
                    Button {
                        text: "Печать отчета"
                        onClicked: {
                            var index = executionsListView.currentIndex;
                            if (index !== -1) {
                                var executionId = executionsModel.get(index).id;
                                // TODO: Печать отчета
                                console.log("QML CalendarView: Запрошено печать отчета по execution'у ID", executionId);
                            }
                        }
                    }
                    
                    Item {
                        Layout.fillWidth: true // Заполнитель
                    }
                }
                // --- ---
            }
        }
        // --- ---
    }

    /**
     * Загружает список выполненных алгоритмов (executions) за заданную дату из Python
     * @param {string} dateString - Дата в формате 'YYYY-MM-DD'
     */
    function loadExecutionsForDate(dateString) {
        console.log("QML CalendarView: Запрос списка execution'ов за дату", dateString, "у Python...");
        var executionsList = appData.getExecutionsByDate(dateString);
        console.log("QML CalendarView: Получен список execution'ов из Python (сырой):", JSON.stringify(executionsList).substring(0, 500));

        // Преобразование QJSValue/QVariant в массив JS
        if (executionsList && typeof executionsList === 'object' && executionsList.hasOwnProperty('toVariant')) {
            executionsList = executionsList.toVariant();
            console.log("QML CalendarView: QJSValue (executionsList) преобразован в:", JSON.stringify(executionsList).substring(0, 500));
        }

        // Очищаем текущую модель
        executionsModel.clear();
        console.log("QML CalendarView: Модель ListView execution'ов очищена.");

        // --- Более гибкая проверка на "массивоподобность" ---
        if (executionsList && typeof executionsList === 'object' && executionsList.length !== undefined) {
        // --- ---
            var count = executionsList.length;
            console.log("QML CalendarView: Полученный список execution'ов является массивоподобным. Количество элементов:", count);
            
            for (var i = 0; i < count; i++) {
                var execution = executionsList[i];
                console.log("QML CalendarView: Обрабатываем execution", i, ":", JSON.stringify(execution).substring(0, 200));
                
                if (typeof execution === 'object' && execution !== null) {
                    try {
                        executionsModel.append({
                            "id": execution["id"],
                            "algorithm_id": execution["algorithm_id"],
                            "algorithm_name": execution["algorithm_name"] || "",
                            "started_at": execution["started_at"] || "",
                            "started_at_display": execution["started_at_display"] || "", // Форматированное время начала
                            "completed_at": execution["completed_at"] || "",
                            "completed_at_display": execution["completed_at_display"] || "", // Форматированное время окончания
                            "status": execution["status"] || "unknown",
                            "created_by_user_id": execution["created_by_user_id"] || null,
                            "created_by_user_display_name": execution["created_by_user_display_name"] || "Неизвестен"
                            // Добавьте другие поля, если они нужны для отображения в списке
                        });
                        console.log("QML CalendarView: Execution", i, "добавлен в модель.");
                    } catch (e) {
                        console.error("QML CalendarView: Ошибка при добавлении execution", i, "в модель:", e.toString(), "Данные:", JSON.stringify(execution));
                    }
                } else {
                    console.warn("QML CalendarView: Execution", i, "не является корректным объектом:", typeof execution, execution);
                }
            }
        } else {
            console.error("QML CalendarView: Python не вернул корректный массивоподобный объект для execution'ов. Получен тип:", typeof executionsList, "Значение:", executionsList);
        }
        console.log("QML CalendarView: Модель ListView execution'ов обновлена. Элементов:", executionsModel.count);
    }

    Component.onCompleted: {
        console.log("QML CalendarView: Загружен. Инициализация...");
        // При загрузке компонента загружаем список execution'ов за текущую дату
        calendarViewRoot.loadExecutionsForDate(Qt.formatDate(calendarViewRoot.selectedDate, "yyyy-MM-dd"));
    }
}