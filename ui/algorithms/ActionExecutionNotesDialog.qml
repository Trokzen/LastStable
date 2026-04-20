// ui/algorithms/ActionExecutionNotesDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5

Dialog {
    id: notesDialog
    title: "Примечания к действию"
    width: 400
    height: 250
    standardButtons: Dialog.Ok | Dialog.Cancel

    property int actionExecutionId: -1
    property string initialNotes: ""

    signal notesSaved()

    TextArea {
        id: notesTextArea
        text: notesDialog.initialNotes
        wrapMode: TextEdit.Wrap
        selectByMouse: true
        anchors.fill: parent
        anchors.margins: 10
        placeholderText: "Введите примечания..."
    }

    onAccepted: {
        // Подготавливаем данные для updateActionExecution
        var updateData = {
            "notes": notesTextArea.text
        };
        // Используем существующий метод
        if (appData.updateActionExecution) {
            appData.updateActionExecution(actionExecutionId, updateData);
        } else {
            console.warn("Метод updateActionExecution не найден в appData");
        }
        // Сигнал для обновления таблицы (без передачи текста)
        notesSaved(); // ← убрали аргумент
    }
}