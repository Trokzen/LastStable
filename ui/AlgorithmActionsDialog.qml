// ui/AlgorithmActionsDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5
import "." // Импорт из той же директории

Popup {
    id: algorithmActionsDialog
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    width: Math.max(800, Math.min(parent.width * 1, 900))
    height: Math.max(600, Math.min(parent.height * 1, 600))
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape // | Popup.CloseOnPressOutsideParent // Отключим закрытие по клику снаружи

    // Свойства
    property int currentAlgorithmId: -1
    property string currentAlgorithmName: ""
    property string currentAlgorithmTimeType: "" 

    background: Rectangle {
        color: "white"
        border.color: "lightgray"
        radius: 5
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        // Заголовок
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 40 // Фиксированная высота для заголовка
            
            Label {
                text: "Действия алгоритма: " + currentAlgorithmName
                font.pointSize: 12
                font.bold: true
                elide: Text.ElideRight
            }
            Item {
                Layout.fillWidth: true
            }
            Button {
                text: "Закрыть"
                onClicked: {
                    console.log("QML AlgorithmActionsDialog: Нажата кнопка Закрыть");
                    algorithmActionsDialog.close();
                }
            }
        }

        // Основная область с AlgorithmActionsView
        AlgorithmActionsView {
            id: algorithmActionsView
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentAlgorithmId: algorithmActionsDialog.currentAlgorithmId
            currentAlgorithmName: algorithmActionsDialog.currentAlgorithmName
            currentAlgorithmTimeType: algorithmActionsDialog.currentAlgorithmTimeType
            
            // Подключаем сигналы
            onAddActionRequested: {
                console.log("QML AlgorithmActionsDialog: Запрошено добавление действия для алгоритма ID:", currentAlgorithmId);
                actionEditorDialog.resetForAdd(currentAlgorithmId);
                actionEditorDialog.open();
            }
            
            onEditActionRequested: {
                console.log("QML AlgorithmActionsDialog: Запрошено редактирование действия:", actionData);
                actionEditorDialog.loadDataForEdit(actionData);
                actionEditorDialog.open();
            }
            
            onDeleteActionRequested: {
                console.log("QML AlgorithmActionsDialog: Запрошено удаление действия ID:", actionId);
                // TODO: Добавить подтверждение
                var confirmDelete = true; // Пока без подтверждения
                if (confirmDelete) {
                    var result = appData.deleteAction(actionId);
                    if (result === true) {
                        console.log("QML AlgorithmActionsDialog: Действие ID", actionId, "удалено успешно.");
                        algorithmActionsView.removeAction(actionId);
                    } else if (typeof result === 'string') {
                        console.warn("QML AlgorithmActionsDialog: Ошибка удаления действия:", result);
                        // TODO: Отобразить ошибку пользователю
                    } else {
                         console.error("QML AlgorithmActionsDialog: Неизвестная ошибка удаления действия. Результат:", result);
                    }
                }
            }
            
            onDuplicateActionRequested: {
                console.log("QML AlgorithmActionsDialog: Запрошено дублирование действия ID:", actionId);
                var newActionId = appData.duplicateAction(actionId); // Дублируем в том же алгоритме
                if (typeof newActionId === 'number' && newActionId > 0) {
                    console.log("QML AlgorithmActionsDialog: Действие ID", actionId, "дублировано успешно. Новый ID:", newActionId);
                    // Перезагружаем список действий, чтобы увидеть новую копию
                    algorithmActionsView.loadActions();
                } else {
                    console.warn("QML AlgorithmActionsDialog: Ошибка дублирования действия ID", actionId, ". Результат:", newActionId);
                    // TODO: Отобразить ошибку пользователю
                }
            }
        }
        
        // Диалог редактора действия
        ActionEditorDialog {
            id: actionEditorDialog
            // Подключаемся к сигналу сохранения, чтобы обновить список
            onActionSaved: {
                console.log("QML AlgorithmActionsDialog: Получен сигнал actionSaved от ActionEditorDialog. Перезагружаем список действий.");
                algorithmActionsView.loadActions();
            }
        }
    }

    /**
     * Загружает данные для диалога
     */
    function loadData(algorithmData) {
        console.log("QML AlgorithmActionsDialog: Загрузка данных для алгоритма:", JSON.stringify(algorithmData));
        currentAlgorithmId = algorithmData.id;
        currentAlgorithmName = algorithmData.name || "Без названия";
        // --- НОВОЕ: Установка типа времени ---
        currentAlgorithmTimeType = algorithmData.time_type || "Не задан"; 
        // --- ---
        // После установки currentAlgorithmId, AlgorithmActionsView автоматически попытается загрузить действия
        // Но лучше вызвать явно, чтобы быть уверенным
        if (algorithmActionsView && typeof algorithmActionsView.loadActions === 'function') {
            algorithmActionsView.loadActions();
        } else {
            console.warn("QML AlgorithmActionsDialog: AlgorithmActionsView или его метод loadActions не найдены при загрузке данных.");
        }
    }

    onOpened: {
        console.log("QML AlgorithmActionsDialog: Диалог открыт. ID алгоритма:", currentAlgorithmId);
        // Убедимся, что список действий загружен
        if (currentAlgorithmId > 0) {
            algorithmActionsView.loadActions();
        }
    }
    
    onClosed: {
        console.log("QML AlgorithmActionsDialog: Диалог закрыт.");
        // Опционально: сброс данных
        currentAlgorithmId = -1;
        currentAlgorithmName = "";
    }
}