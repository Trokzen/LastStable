// ui/algorithms/UserSelectionDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Dialog {
    id: userSelectionDialog
    
    // --- Свойства ---
    property var usersList: []  // Список всех пользователей
    property int currentUserId: -1  // Текущий выбранный пользователь
    property int executionId: -1  // ID execution'а, для которого выбирается пользователь
    // --- ---
    
    // --- Сигналы ---
    signal userSelected(int userId)  // Сигнал при выборе пользователя
    // --- ---
    
    title: "Выбор ответственного пользователя"
    width: 500
    height: 400
    modal: true
    focus: true
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10
        
        // --- Список пользователей ---
        ListView {
            id: usersListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            model: usersList.length > 0 ? usersList : []
            
            delegate: ItemDelegate {
                width: usersListView.width
                height: 30
                
                // Формируем отображаемое имя: "Звание Фамилия И.О."
                text: modelData.rank + " " + modelData.last_name + " " + 
                      (modelData.first_name ? modelData.first_name.charAt(0) + "." : "") +
                      (modelData.middle_name ? modelData.middle_name.charAt(0) + "." : "")
                
                highlighted: modelData.id === userSelectionDialog.currentUserId
                
                onClicked: {
                    userSelectionDialog.currentUserId = modelData.id;
                    console.log("QML UserSelectionDialog: Выбран пользователь ID:", modelData.id, "(", text, ")");
                }
            }
            
            ScrollBar.vertical: ScrollBar {}
        }
        // --- ---
        
        // --- Кнопки ---
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            
            Item { Layout.fillWidth: true } // Заполнитель
            
            Button {
                text: "OK"
                enabled: userSelectionDialog.currentUserId > 0
                onClicked: {
                    if (userSelectionDialog.currentUserId > 0) {
                        console.log("QML UserSelectionDialog: Подтверждение выбора пользователя ID:", userSelectionDialog.currentUserId);
                        userSelectionDialog.userSelected(userSelectionDialog.currentUserId);
                        userSelectionDialog.close();
                    } else {
                        console.warn("QML UserSelectionDialog: Нет выбранного пользователя для подтверждения.");
                    }
                }
            }
            
            Button {
                text: "Отмена"
                onClicked: {
                    console.log("QML UserSelectionDialog: Отмена выбора пользователя.");
                    userSelectionDialog.close();
                }
            }
        }
        // --- ---
    }
    
    // При открытии диалога устанавливаем фокус на список
    onOpened: {
        usersListView.forceActiveFocus();
    }
}