// ui/AlgorithmEditorDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Popup {
    id: algorithmEditorDialog
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    width: Math.min(parent.width * 0.8, 600)
    height: Math.min(parent.height * 0.8, 400)
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // Свойства
    property bool isEditMode: false
    property int currentAlgorithmId: -1

    // Сигнал для уведомления о сохранении
    signal algorithmSaved()

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
            text: isEditMode ? "Редактировать алгоритм" : "Добавить новый алгоритм"
            font.pointSize: 14
            font.bold: true
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columnSpacing: 10
            rowSpacing: 10
            columns: 2

            Label {
                text: "Название:*"
                Layout.alignment: Qt.AlignRight
            }
            TextField {
                id: nameField
                Layout.fillWidth: true
                placeholderText: "Введите название алгоритма..."
            }

            Label {
                text: "Категория:*"
                Layout.alignment: Qt.AlignRight
            }
            ComboBox {
                id: categoryComboBox
                Layout.fillWidth: true
                model: ["повседневная деятельность", "боевая готовность", "противодействие терроризму", "кризисные ситуации"]
            }

            Label {
                text: "Тип времени:*"
                Layout.alignment: Qt.AlignRight
            }
            ComboBox {
                id: timeTypeComboBox
                Layout.fillWidth: true
                model: ["оперативное", "астрономическое"]
            }

            Label {
                text: "Описание:"
                Layout.alignment: Qt.AlignRight | Qt.AlignTop
            }
            TextArea {
                id: descriptionArea
                Layout.fillWidth: true
                Layout.fillHeight: true
                placeholderText: "Введите описание алгоритма..."
                wrapMode: TextArea.Wrap
                background: Rectangle {
                    border.color: descriptionArea.activeFocus ? "#3498db" : "#ccc" // Цвет границы при фокусе (синий) и без (серый)
                    border.width: 1 // Толщина границы в пикселях
                    radius: 2 // Небольшое скругление углов (опционально)
                    color: "white" // Цвет фона поля ввода
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
                Layout.fillWidth: true
            }
            Button {
                text: "Отмена"
                onClicked: {
                    console.log("QML AlgorithmEditorDialog: Нажата кнопка Отмена")
                    algorithmEditorDialog.close()
                }
            }
            Button {
                text: isEditMode ? "Сохранить" : "Добавить"
                onClicked: {
                    console.log("QML AlgorithmEditorDialog: Нажата кнопка Сохранить/Добавить")
                    errorMessageLabel.text = ""

                    // Валидация
                    if (!nameField.text.trim()) {
                        errorMessageLabel.text = "Пожалуйста, заполните название алгоритма."
                        return
                    }
                    if (categoryComboBox.currentIndex === -1) {
                        errorMessageLabel.text = "Пожалуйста, выберите категорию."
                        return
                    }
                    if (timeTypeComboBox.currentIndex === -1) {
                        errorMessageLabel.text = "Пожалуйста, выберите тип времени."
                        return
                    }

                    // Подготавливаем данные
                    var algorithmData = {
                        "name": nameField.text.trim(),
                        "category": categoryComboBox.currentText,
                        "time_type": timeTypeComboBox.currentText,
                        "description": descriptionArea.text
                    }

                    var result
                    if (isEditMode) {
                        console.log("QML AlgorithmEditorDialog: Отправляем обновление алгоритма ID", currentAlgorithmId, "в Python:", JSON.stringify(algorithmData))
                        result = appData.updateAlgorithm(currentAlgorithmId, algorithmData)
                    } else {
                        console.log("QML AlgorithmEditorDialog: Отправляем новый алгоритм в Python:", JSON.stringify(algorithmData))
                        result = appData.addAlgorithm(algorithmData)
                    }

                    if (result === true || (typeof result === 'number' && result > 0)) {
                        console.log("QML AlgorithmEditorDialog: Алгоритм успешно сохранен/добавлен. Результат:", result)
                        algorithmEditorDialog.algorithmSaved()
                        algorithmEditorDialog.close()
                    } else {
                        var errorMsg = "Неизвестная ошибка"
                        if (typeof result === 'string') {
                            errorMsg = result
                        } else if (result === false) {
                            errorMsg = "Не удалось выполнить операцию. Проверьте данные."
                        } else if (result === -1) {
                            errorMsg = "Ошибка при добавлении алгоритма."
                        }
                        errorMessageLabel.text = "Ошибка: " + errorMsg
                        console.warn("QML AlgorithmEditorDialog: Ошибка при сохранении/добавлении алгоритма:", errorMsg)
                    }
                }
            }
        }
    }

    /**
     * Сбрасывает диалог для добавления нового алгоритма
     */
    function resetForAdd() {
        console.log("QML AlgorithmEditorDialog: Сброс для добавления нового алгоритма")
        isEditMode = false
        currentAlgorithmId = -1
        nameField.text = ""
        categoryComboBox.currentIndex = -1
        timeTypeComboBox.currentIndex = -1
        descriptionArea.text = ""
        errorMessageLabel.text = ""
    }

    /**
     * Загружает данные алгоритма для редактирования
     */
    function loadDataForEdit(algorithmData) {
        console.log("QML AlgorithmEditorDialog: Загрузка данных для редактирования:", JSON.stringify(algorithmData))
        isEditMode = true
        currentAlgorithmId = algorithmData.id
        nameField.text = algorithmData.name || ""
        // Найдем индекс категории
        var catIndex = categoryComboBox.indexOfValue(algorithmData.category)
        categoryComboBox.currentIndex = catIndex !== -1 ? catIndex : -1
        // Найдем индекс типа времени
        var timeIndex = timeTypeComboBox.indexOfValue(algorithmData.time_type)
        timeTypeComboBox.currentIndex = timeIndex !== -1 ? timeIndex : -1
        descriptionArea.text = algorithmData.description || ""
        errorMessageLabel.text = ""
    }

    onOpened: {
        console.log("QML AlgorithmEditorDialog: Диалог открыт.")
        errorMessageLabel.text = ""
    }
}