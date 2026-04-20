import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Dialog {
    id: aboutDialog
    title: "О программе"
    width: 500
    height: 400
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    background: Rectangle {
        color: "white"
        border.color: "#bdc3c7"
        radius: 8
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        Text {
            Layout.fillWidth: true
            text: "ВПО «Алгоритм-ДЧ»"
            font.pixelSize: 18
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            color: "#2c3e50"
        }

        Text {
            Layout.fillWidth: true
            text: "Программное обеспечение обеспечивает автоматизацию процесса дежурства по организации и позволяет эффективно управлять мероприятиями в различных режимах: повседневная деятельность, боевая готовность, противодействие терроризму и кризисные ситуации."
            font.pixelSize: 12
            wrapMode: Text.Wrap
            color: "#34495e"
        }

        Text {
            Layout.fillWidth: true
            text: "Основные возможности:\n\n• Управление мероприятиями и задачами\n• Отслеживание выполнения мероприятий\n• Настройка параметров приложения\n• Добавление и редактирование данных \n• Генерация отчетов и печать"
            font.pixelSize: 11
            wrapMode: Text.Wrap
            color: "#34495e"
        }

        Text {
            Layout.fillWidth: true
            text: "Версия: 1.1\n\n© 2026, Все права защищены"
            font.pixelSize: 10
            wrapMode: Text.Wrap
            color: "#7f8c8d"
            Layout.alignment: Qt.AlignBottom
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Item { Layout.fillWidth: true }
            Button {
                text: "Закрыть"
                onClicked: aboutDialog.close()
            }
        }
    }
}