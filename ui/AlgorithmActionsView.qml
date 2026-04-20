// ui/AlgorithmActionsView.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Item {
    id: algorithmActionsViewRoot

    // Свойства для получения ID и типа времени текущего алгоритма
    property int currentAlgorithmId: -1
    property string currentAlgorithmName: ""
    property string currentAlgorithmTimeType: "" // Для отображения типа времени
    property int currentActionRow: -1
    property int currentActionIndex: -1

    ListModel {
        id: actionsModel
        // Модель будет заполнена данными из Python
    }

    // Сигналы для уведомления родителя о действиях
    signal addActionRequested()
    signal editActionRequested(var actionData)
    signal deleteActionRequested(var actionId)
    signal duplicateActionRequested(var actionId)

    RowLayout {
        anchors.fill: parent
        spacing: 10

        // --- Основная область: Заголовок и список действий (75% ширины) ---
        ColumnLayout {
            Layout.preferredWidth: parent.width * 0.75 // 75% ширины
            Layout.fillHeight: true
            spacing: 10

            // --- ИЗМЕНЕН ЗАГОЛОВОК ---
            Label {
                // text: "Действия алгоритма: " + currentAlgorithmName + " (" + currentAlgorithmTimeType + ")" // Старый вариант
                text: "Время: " + currentAlgorithmTimeType // Новый вариант
                font.pointSize: 14
                font.bold: true
                elide: Text.ElideRight
            }
            // --- ---

            // --- ТАБЛИЦА ДЕЙСТВИЙ (заменить существующую секцию) ---
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                // Заголовки таблицы
                Rectangle {
                    Layout.fillWidth: true
                    height: 30
                    color: "#e0e0e0"
                    border.color: "#ccc"
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 1
                        spacing: 1
                        
                        Rectangle {
                            Layout.preferredWidth: parent.width * 0.5 - 2
                            height: parent.height
                            color: "transparent"
                            border.color: "#ccc"
                            Text {
                                anchors.centerIn: parent
                                text: "Наименование"
                                font.bold: true
                                font.pixelSize: 12
                            }
                        }
                        Rectangle {
                            Layout.preferredWidth: parent.width * 0.25 - 1
                            height: parent.height
                            color: "transparent"
                            border.color: "#ccc"
                            Text {
                                anchors.centerIn: parent
                                text: "Время начала"
                                font.bold: true
                                font.pixelSize: 12
                            }
                        }
                        Rectangle {
                            Layout.preferredWidth: parent.width * 0.25 - 1
                            height: parent.height
                            color: "transparent"
                            border.color: "#ccc"
                            Text {
                                anchors.centerIn: parent
                                text: "Время окончания"
                                font.bold: true
                                font.pixelSize: 12
                            }
                        }
                    }
                }

                // Содержимое таблицы (ListView с горизонтальным делегатом)
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    
                    ListView {
                        id: actionsListView
                        model: actionsModel
                        boundsBehavior: Flickable.StopAtBounds

                        delegate: Item {
                            width: actionsListView.width
                            height: 35 // Немного увеличенная высота для лучшей читаемости

                            Rectangle {
                                anchors.fill: parent
                                // Цвет фона строки (чередующийся + выделение)
                                color: index % 2 ? "#f9f9f9" : "#ffffff"
                                border.color: actionsListView.currentIndex === index ? "#3498db" : "#ddd"

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 1
                                    spacing: 1

                                    // --- Столбец 1: Наименование ---
                                    Rectangle {
                                        Layout.preferredWidth: parent.width * 0.5 - 2
                                        height: parent.height
                                        color: "transparent"
                                        Text {
                                            anchors.left: parent.left
                                            anchors.leftMargin: 5
                                            anchors.right: parent.right
                                            anchors.rightMargin: 5
                                            anchors.verticalCenter: parent.verticalCenter
                                            color: "black" // Всегда черный
                                            text: algorithmActionsViewRoot.cleanSingleLineText(model.description || "")
                                            elide: Text.ElideRight
                                            font.pixelSize: 11
                                            font.bold: true // Оставляем жирный шрифт
                                        }
                                    }
                                    // --- Столбец 2: Время начала ---
                                    Rectangle {
                                        Layout.preferredWidth: parent.width * 0.25 - 1
                                        height: parent.height
                                        color: "transparent"
                                        Text {
                                            anchors.centerIn: parent
                                            color: "gray" // Всегда серый
                                            // --- ---
                                            text: {
                                                var startTime = model.start_offset;
                                                if (startTime === undefined || startTime === null || startTime === "") {
                                                    return "00:00:00";
                                                }
                                                return String(startTime);
                                            }
                                            elide: Text.ElideRight
                                            font.pixelSize: 11
                                        }
                                    }
                                    // --- Столбец 3: Время окончания ---
                                    Rectangle {
                                        Layout.preferredWidth: parent.width * 0.25 - 1
                                        height: parent.height
                                        color: "transparent"
                                        Text {
                                            anchors.centerIn: parent
                                            color: "gray" // Всегда серый
                                            // --- ---
                                            text: {
                                                var endTime = model.end_offset;
                                                if (endTime === undefined || endTime === null || endTime === "") {
                                                    return "00:00:00";
                                                }
                                                return String(endTime);
                                            }
                                            elide: Text.ElideRight
                                            font.pixelSize: 11
                                        }
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        actionsListView.currentIndex = index;
                                    }
                                    onDoubleClicked: {
                                        actionsListView.currentIndex = index;
                                        // Убедитесь, что actionsModel определен в корне AlgorithmActionsView
                                        var actionData = actionsModel.get(index); 
                                        algorithmActionsViewRoot.editActionRequested(actionData);
                                    }
                                }
                            }
                        }
                    }
                }
            }
            // --- ---
        }
        // --- ---

        // --- Панель кнопок справа (25% ширины) ---
        ColumnLayout {
            Layout.preferredWidth: parent.width * 0.25 // 25% ширины
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignTop
            spacing: 10

            Button {
                text: "Добавить"
                Layout.fillWidth: true
                onClicked: algorithmActionsViewRoot.addActionRequested()
            }

            // Обновить обработчики кнопок (найти и заменить в файле)
            Button {
                text: "Редактировать"
                Layout.fillWidth: true
                enabled: actionsListView.currentIndex >= 0 && actionsListView.currentIndex < actionsModel.count
                onClicked: {
                    var index = actionsListView.currentIndex;
                    if (index >= 0 && index < actionsModel.count) {
                        var actionData = actionsModel.get(index);
                        algorithmActionsViewRoot.editActionRequested(actionData);
                    }
                }
            }

            Button {
                text: "Удалить"
                Layout.fillWidth: true
                enabled: actionsListView.currentIndex >= 0 && actionsListView.currentIndex < actionsModel.count
                onClicked: {
                    var index = actionsListView.currentIndex;
                    if (index >= 0 && index < actionsModel.count) {
                        var actionId = actionsModel.get(index).id;
                        algorithmActionsViewRoot.deleteActionRequested(actionId);
                    }
                }
            }

            Button {
                text: "Дублировать"
                Layout.fillWidth: true
                enabled: actionsListView.currentIndex >= 0 && actionsListView.currentIndex < actionsModel.count
                onClicked: {
                    var index = actionsListView.currentIndex;
                    if (index >= 0 && index < actionsModel.count) {
                        var actionId = actionsModel.get(index).id;
                        algorithmActionsViewRoot.duplicateActionRequested(actionId);
                    }
                }
            }
            
            Item {
                Layout.fillHeight: true // Заполнитель для выравнивания кнопок сверху
            }
        }
        // --- ---
    }

    // ... (остальные функции loadActions, updateOrAddAction, removeAction остаются без изменений) ...
    // Или копируются из вашего текущего файла если они были изменены.

    /**
     * Загружает список действий для текущего алгоритма из Python
     */
    function loadActions() {
        if (currentAlgorithmId <= 0) {
            console.warn("QML AlgorithmActionsView: Невозможно загрузить действия, ID алгоритма не задан или некорректен:", currentAlgorithmId);
            return;
        }
        
        console.log("QML AlgorithmActionsView: === НАЧАЛО ЗАГРУЗКИ СПИСКА ДЕЙСТВИЙ ===");
        console.log("QML AlgorithmActionsView: 1. Запрос списка действий для алгоритма ID", currentAlgorithmId, "у Python...");
        
        var actionsList = appData.getActionsByAlgorithmId(currentAlgorithmId);
        
        console.log("QML AlgorithmActionsView: 2. Получен список действий из Python (сырой):", JSON.stringify(actionsList).substring(0, 500));

        // --- Преобразование QJSValue/QVariant в массив JS ---
        console.log("QML AlgorithmActionsView: 3. Проверка необходимости преобразования QJSValue...");
        if (actionsList && typeof actionsList === 'object' && typeof actionsList.hasOwnProperty === 'function' && actionsList.hasOwnProperty('toVariant')) {
            console.log("QML AlgorithmActionsView: 3a. Обнаружен QJSValue, преобразование в QVariant/JS...");
            actionsList = actionsList.toVariant();
            console.log("QML AlgorithmActionsView: 3b. QJSValue (actionsList) преобразован в:", JSON.stringify(actionsList).substring(0, 500));
        } else {
            console.log("QML AlgorithmActionsView: 3a. Преобразование не требуется или невозможно.");
        }
        // --- ---

        // --- Очистка модели ---
        console.log("QML AlgorithmActionsView: 4. Очистка модели ListView действий...");
        if (typeof actionsModel === 'undefined') {
            console.error("QML AlgorithmActionsView: 4a. ОШИБКА - actionsModel не определен!");
            console.log("QML AlgorithmActionsView: === КОНЕЦ ЗАГРУЗКИ СПИСКА ДЕЙСТВИЙ (С ОШИБКОЙ) ===");
            return;
        }
        var oldCount = actionsModel.count;
        actionsModel.clear();
        console.log("QML AlgorithmActionsView: 4b. Модель очищена. Было элементов:", oldCount, "Стало:", actionsModel.count);
        // --- ---

        // --- Заполнение модели ---
        console.log("QML AlgorithmActionsView: 5. Попытка заполнения модели...");
        
        // --- ИЗМЕНЕНО: Более гибкая проверка на "массивоподобность" ---
        // Вместо Array.isArray, проверяем, есть ли у объекта свойство length (не undefined)
        // Это работает как для JS Array, так и для QVariantList, переданного из Python
        if (actionsList && typeof actionsList === 'object' && actionsList.length !== undefined) {
        // --- ---
            var count = actionsList.length;
            console.log("QML AlgorithmActionsView: 5a. Полученный список является массивоподобным. Количество элементов:", count);
            
            if (count === 0) {
                console.log("QML AlgorithmActionsView: 5b. Список действий пуст.");
            }
            
            // --- Заполняем модель данными по одному ---
            for (var i = 0; i < count; i++) {
                var action = actionsList[i];
                console.log("QML AlgorithmActionsView: 5c. Обрабатываем элемент", i, ":", JSON.stringify(action).substring(0, 200)); // Лог каждого элемента
                
                // --- Убедимся, что элемент - это объект ---
                if (typeof action === 'object' && action !== null) {
                // --- ---
                    // --- ИЗМЕНЕНО: Явное копирование свойств с обработкой времени ---
                    // Вместо actionsModel.append(action), создаем новый JS объект
                    // Это помогает избежать проблем с QJSValue/QVariantMap, которые могут
                    // не сериализоваться корректно внутри ListModel.
                    // Также обрабатываем пустые строки для start_offset и end_offset.
                    try {
                        var startOffsetValue = action["start_offset"];
                        var endOffsetValue = action["end_offset"];
                        
                        // Логика обработки значений времени:
                        // 1. Если значение undefined, null или пустая строка, оставляем как есть для делегата
                        //    (делегат должен отображать "00:00:00" или другое значение по умолчанию).
                        // 2. Если это валидная строка (не пустая), передаем ее как есть.
                        // ВАЖНО: Не заменяем на "00:00:00" здесь, пусть делегат решает, что показывать.
                        // Просто убедимся, что это строки или null/undefined.
                        
                        // Преобразуем в строку, если это не undefined/null
                        if (startOffsetValue !== undefined && startOffsetValue !== null) {
                            startOffsetValue = String(startOffsetValue);
                        }
                        if (endOffsetValue !== undefined && endOffsetValue !== null) {
                            endOffsetValue = String(endOffsetValue);
                        }
                        
                        var actionCopy = ({
                            "id": action["id"],
                            "algorithm_id": action["algorithm_id"],
                            "description": action["description"] || "",
                            "technical_text": action["technical_text"] || "",
                            "start_offset": startOffsetValue, // Может быть строкой, null или undefined
                            "end_offset": endOffsetValue,     // Может быть строкой, null или undefined
                            "contact_phones": action["contact_phones"] || "",
                            "report_materials": action["report_materials"] || ""
                            // Добавьте другие поля, если они нужны для отображения в списке
                        });
                        // --- ---
                        
                        actionsModel.append(actionCopy); // <-- Добавляем КОПИЮ
                        console.log("QML AlgorithmActionsView: 5d. Элемент", i, "добавлен в модель.");
                    } catch (e_append) {
                        console.error("QML AlgorithmActionsView: 5e. ОШИБКА при добавлении элемента", i, "в модель:", e_append.toString(), "Данные:", JSON.stringify(action));
                    }
                } else {
                    console.warn("QML AlgorithmActionsView: 5f. Элемент", i, "не является корректным объектом:", typeof action, action);
                }
                // --- ---
            }
            // --- ---
        } else {
            // --- ИЗМЕНЕНО: Сообщение об ошибке ---
            console.error("QML AlgorithmActionsView: 5b. ОШИБКА: Python не вернул корректный массивоподобный объект. Получен тип:", typeof actionsList, "Значение:", actionsList);
            // --- ---
        }
        console.log("QML AlgorithmActionsView: 6. Модель ListView действий обновлена. Элементов:", actionsModel.count);
        // --- ---

        // --- ДОБАВЛЕНО: Отладка содержимого модели ---
        if (actionsModel.count > 0) {
            try {
                console.log("QML AlgorithmActionsView: 7. Первый элемент в модели (попытка):", JSON.stringify(actionsModel.get(0)));
            } catch (e_get) {
                console.warn("QML AlgorithmActionsView: 7a. Не удалось сериализовать первый элемент модели для лога:", e_get.toString());
                // Попробуем получить отдельные свойства
                var firstItem = actionsModel.get(0);
                if (firstItem) {
                    console.log("QML AlgorithmActionsView: 7b. Первый элемент в модели (свойства): id=", firstItem.id, "description=", firstItem.description, "start_offset=", firstItem.start_offset, "end_offset=", firstItem.end_offset);
                }
            }
        }
        // --- ---
        
        console.log("QML AlgorithmActionsView: === КОНЕЦ ЗАГРУЗКИ СПИСКА ДЕЙСТВИЙ ===");
    }

    function cleanSingleLineText(text) {
        if (typeof text !== 'string') return '';
        // Заменяем все переводы строк и табуляции на пробелы
        return text.replace(/[\r\n\t]+/g, ' ')
                .replace(/\s+/g, ' ') // схлопываем множественные пробелы
                .trim();
    }

    /**
     * Обновляет или добавляет действие в модель
     */
    function updateOrAddAction(actionData) {
        if (!actionData || !actionData.id) {
            console.warn("QML AlgorithmActionsView: updateOrAddAction - некорректные данные действия:", JSON.stringify(actionData));
            return;
        }
        
        // Проверяем, существует ли уже действие с таким ID
        for (var i = 0; i < actionsModel.count; i++) {
            if (actionsModel.get(i).id === actionData.id) {
                // Обновляем существующий
                actionsModel.set(i, actionData);
                console.log("QML AlgorithmActionsView: Действие ID", actionData.id, "обновлено в модели.");
                return;
            }
        }
        // Добавляем новый (если он принадлежит текущему алгоритму)
        if (actionData.algorithm_id === currentAlgorithmId) {
            actionsModel.append(actionData);
            console.log("QML AlgorithmActionsView: Новое действие ID", actionData.id, "добавлено в модель.");
        } else {
             console.log("QML AlgorithmActionsView: Новое действие ID", actionData.id, "не добавлено в модель, так как принадлежит другому алгоритму (", actionData.algorithm_id, ").");
        }
    }

    /**
     * Удаляет действие из модели
     */
    function removeAction(actionId) {
        for (var i = 0; i < actionsModel.count; i++) {
            if (actionsModel.get(i).id === actionId) {
                actionsModel.remove(i);
                console.log("QML AlgorithmActionsView: Действие ID", actionId, "удалено из модели.");
                // Сбрасываем выбор, если удалили выбранный элемент
                if (actionsListView.currentIndex === i) {
                    actionsListView.currentIndex = -1;
                }
                return;
            }
        }
    }
}