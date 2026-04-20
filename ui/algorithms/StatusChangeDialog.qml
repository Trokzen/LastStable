// ui/algorithms/StatusChangeDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Popup {
    id: statusChangeDialog
    width: 400
    height: 420
    // Привязываемся к глобальному оверлею приложения, чтобы быть поверх всех модалок
    parent: Overlay.overlay
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    property int actionExecutionId: -1
    property string currentStatus: ""

    signal statusChanged(int actionExecutionId, string newStatus)

    background: Rectangle {
        radius: 12
        color: "#ffffff"
        border.color: "#e0e0e0"
        border.width: 1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        Label {
            text: "Изменить статус мероприятия"
            font.pointSize: 16
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#dee2e6"
        }

        Label {
            text: "Текущий статус:"
            font.pixelSize: 13
            color: "#666"
        }

        Rectangle {
            Layout.fillWidth: true
            height: 40
            radius: 8
            color: getStatusColor(statusChangeDialog.currentStatus)

            Label {
                anchors.centerIn: parent
                text: getStatusText(statusChangeDialog.currentStatus)
                color: "#ffffff"
                font.pixelSize: 16
                font.bold: true
            }
        }

        Label {
            text: "Выберите новый статус:"
            font.pixelSize: 13
            color: "#666"
            Layout.topMargin: 5
        }

        // Кнопки выбора статуса
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: [
                    { "status": "pending", "text": "⏸ Ожидает", "color": "#3498db" },
                    { "status": "in_progress", "text": "🔄 В процессе", "color": "#f39c12" },
                    { "status": "completed", "text": "✅ Выполнено", "color": "#27ae60" },
                    { "status": "skipped", "text": "❌ Пропущено", "color": "#e74c3c" }
                ]
                delegate: Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    radius: 8
                    color: modelData.color
                    opacity: statusChangeDialog.currentStatus === modelData.status ? 0.5 : 1.0

                    Text {
                        anchors.centerIn: parent
                        text: modelData.text
                        color: "#ffffff"
                        font.pixelSize: 14
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        enabled: statusChangeDialog.currentStatus !== modelData.status
                        onClicked: {
                            statusChangeDialog.statusChanged(
                                statusChangeDialog.actionExecutionId, 
                                modelData.status
                            )
                            statusChangeDialog.close()
                        }
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }

        // Кнопка отмены
        Rectangle {
            Layout.alignment: Qt.AlignRight
            width: 100
            height: 36
            radius: 8
            color: {
                if (cancelBtn.pressed) return "#95a5a6"
                if (cancelBtn.hovered) return "#bdc3c7"
                return "#ecf0f1"
            }
            Behavior on color { ColorAnimation { duration: 150 } }
            MouseArea {
                id: cancelBtn
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: statusChangeDialog.close()
            }
            Text {
                anchors.centerIn: parent
                text: "Отмена"
                color: "#2c3e50"
                font.pixelSize: 13
                font.bold: true
            }
        }
    }

    function getStatusText(status) {
        switch(status) {
            case "pending": return "⏸ Ожидает"
            case "in_progress": return "🔄 В процессе"
            case "completed": return "✅ Выполнено"
            case "skipped": return "❌ Пропущено"
            default: return "Неизвестно"
        }
    }

    function getStatusColor(status) {
        switch(status) {
            case "pending": return "#3498db"
            case "in_progress": return "#f39c12"
            case "completed": return "#27ae60"
            case "skipped": return "#e74c3c"
            default: return "#95a5a6"
        }
    }
}
