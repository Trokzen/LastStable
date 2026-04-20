// ui/OrganizationEditorDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5
import QtQuick.Dialogs 6.5

Popup {
    id: organizationEditorDialog
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    width: Math.min(parent.width * 0.75, 850)
    height: Math.min(parent.height * 0.9, 750)
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // Свойства
    property bool isEditMode: false
    property int currentOrganizationId: -1

    // Сигналы
    signal organizationSaved()

    // Модель для списка файлов
    ListModel {
        id: referenceFilesListModel
    }

    // Современный фон
    background: Rectangle {
        radius: 12
        color: "#ffffff"
        border.color: "#e0e0e0"
        border.width: 1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0

        // --- Заголовок ---
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "#2c3e50"
            radius: 12
            clip: true

            Label {
                id: dialogTitleLabel
                anchors.centerIn: parent
                text: organizationEditorDialog.isEditMode ? "Редактировать организацию" : "Добавить организацию"
                color: "#ffffff"
                font.pointSize: 16
                font.bold: true
            }
        }

        // --- Разделитель ---
        Rectangle {
            Layout.fillWidth: true
            height: 2
            color: "#34495e"
        }

        // --- Основной контент ---
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            padding: 20

            GridLayout {
                columns: 2
                columnSpacing: 20
                rowSpacing: 15
                width: parent.width

                Label { text: "Название:*" }
                TextField {
                    id: nameField
                    Layout.fillWidth: true
                    placeholderText: "Введите название организации..."
                    font.pixelSize: 13
                    padding: 8
                    background: Rectangle {
                        implicitHeight: 36
                        radius: 6
                        color: "#f8f9fa"
                        border.color: nameField.activeFocus ? "#3498db" : "#dee2e6"
                        border.width: 1
                    }
                }

                Label { text: "Телефон:" }
                TextField {
                    id: phoneField
                    Layout.fillWidth: true
                    placeholderText: "+7 (XXX) XXX-XX-XX"
                    font.pixelSize: 13
                    padding: 8
                    background: Rectangle {
                        implicitHeight: 36
                        radius: 6
                        color: "#f8f9fa"
                        border.color: phoneField.activeFocus ? "#3498db" : "#dee2e6"
                        border.width: 1
                    }
                }

                Label { text: "Контактное лицо:" }
                TextField {
                    id: contactPersonField
                    Layout.fillWidth: true
                    placeholderText: "ФИО контактного лица..."
                    font.pixelSize: 13
                    padding: 8
                    background: Rectangle {
                        implicitHeight: 36
                        radius: 6
                        color: "#f8f9fa"
                        border.color: contactPersonField.activeFocus ? "#3498db" : "#dee2e6"
                        border.width: 1
                    }
                }

                Label { text: "Общие сведения:"; verticalAlignment: Text.AlignTop }
                TextArea {
                    id: notesArea
                    Layout.fillWidth: true
                    Layout.preferredHeight: 120
                    placeholderText: "Введите общие сведения об организации..."
                    wrapMode: TextArea.Wrap
                    font.pixelSize: 13
                    padding: 8
                    background: Rectangle {
                        radius: 6
                        color: "#f8f9fa"
                        border.color: notesArea.activeFocus ? "#3498db" : "#dee2e6"
                        border.width: 1
                    }
                }

                // --- Справочные материалы ---
                Label {
                    text: "Справочные материалы:"
                    Layout.alignment: Qt.AlignRight | Qt.AlignTop
                    verticalAlignment: Text.AlignTop
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    // Список файлов
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.min(referenceFilesColumn.height, 220)
                        radius: 6
                        color: "#f8f9fa"
                        border.color: "#dee2e6"
                        border.width: 1
                        clip: true

                        Flickable {
                            id: filesFlickable
                            anchors.fill: parent
                            anchors.rightMargin: 16 // Отступ для скроллбара
                            contentHeight: referenceFilesColumn.height
                            clip: true

                            Column {
                                id: referenceFilesColumn
                                width: parent.width
                                spacing: 0

                                Repeater {
                                    model: referenceFilesListModel
                                    delegate: Rectangle {
                                        width: parent.width
                                        height: 40
                                        color: index % 2 ? "#ffffff" : "#f8f9fa"

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: 8
                                            anchors.rightMargin: 8
                                            anchors.topMargin: 4
                                            anchors.bottomMargin: 4
                                            spacing: 8

                                            // Иконка типа файла
                                            Rectangle {
                                                width: 28
                                                height: 28
                                                Layout.preferredWidth: 28
                                                Layout.preferredHeight: 28
                                                Layout.alignment: Qt.AlignVCenter
                                                radius: 4
                                                color: {
                                                    var fType = model.file_type || "other"
                                                    if (fType === "word") return "#4a90e2"
                                                    else if (fType === "excel") return "#27ae60"
                                                    else if (fType === "image") return "#e74c3c"
                                                    else if (fType === "pdf") return "#e74c3c"
                                                    else return "#95a5a6"
                                                }
                                                Text {
                                                    anchors.centerIn: parent
                                                    text: {
                                                        var fType = model.file_type || "other"
                                                        if (fType === "word") return "📝"
                                                        else if (fType === "excel") return "📊"
                                                        else if (fType === "image") return "🖼️"
                                                        else if (fType === "pdf") return "📄"
                                                        else return "📎"
                                                    }
                                                    font.pixelSize: 14
                                                }
                                            }

                                            // Имя файла
                                            Text {
                                                Layout.fillWidth: true
                                                Layout.alignment: Qt.AlignVCenter
                                                text: {
                                                    var path = model.file_path || ""
                                                    var parts = path.replace(/\\/g, "/").split("/")
                                                    return parts.length > 0 ? parts[parts.length - 1] : path
                                                }
                                                elide: Text.ElideMiddle
                                                font.pixelSize: 12
                                                verticalAlignment: Text.AlignVCenter
                                            }

                                            // Кнопка убрать из списка
                                            Button {
                                                text: "❌"
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 30
                                                Layout.preferredHeight: 28
                                                Layout.alignment: Qt.AlignVCenter
                                                flat: true
                                                ToolTip.text: "Убрать из списка (файл останется на диске)"
                                                ToolTip.visible: hovered
                                                ToolTip.delay: 500
                                                onClicked: {
                                                    try {
                                                        var fileId = model.id
                                                        if (fileId && fileId > 0) {
                                                            appData.deleteOrganizationReferenceFile(fileId)
                                                            loadReferenceFiles()
                                                        } else {
                                                            console.warn("QML: Некорректный ID файла для удаления из списка:", fileId)
                                                        }
                                                    } catch (e) {
                                                        console.error("QML: Ошибка при удалении файла из списка:", e)
                                                    }
                                                }
                                            }

                                            // Кнопка удалить файл
                                            Button {
                                                text: "🗑️"
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 30
                                                Layout.preferredHeight: 28
                                                Layout.alignment: Qt.AlignVCenter
                                                flat: true
                                                ToolTip.text: "Удалить файл с диска"
                                                ToolTip.visible: hovered
                                                ToolTip.delay: 500
                                                onClicked: {
                                                    try {
                                                        var fileId = model.id
                                                        var filePath = model.file_path
                                                        if (fileId && fileId > 0) {
                                                            fileDeleteConfirmationDialog.fileIdToDelete = fileId
                                                            fileDeleteConfirmationDialog.filePathToDelete = filePath
                                                            fileDeleteConfirmationDialog.open()
                                                        } else {
                                                            console.warn("QML: Некорректный ID файла для полного удаления:", fileId)
                                                        }
                                                    } catch (e) {
                                                        console.error("QML: Ошибка при подготовке удаления файла:", e)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                                // Заглушка, если файлов нет
                                Label {
                                    width: parent.width
                                    text: "Нет прикреплённых файлов"
                                    color: "#95a5a6"
                                    font.pixelSize: 12
                                    font.italic: true
                                    horizontalAlignment: Text.AlignHCenter
                                    padding: 10
                                    visible: referenceFilesListModel.count === 0
                                }
                            }

                            ScrollBar.vertical: ScrollBar {
                                visible: filesFlickable.contentHeight > filesFlickable.height
                            }
                        }
                    }

                    // Кнопка добавить файл
                    Button {
                        text: "➕ Добавить файл..."
                        Layout.alignment: Qt.AlignRight
                        onClicked: {
                            if (organizationEditorDialog.currentOrganizationId > 0) {
                                referenceFileDialog.open()
                            } else {
                                infoMessageDialog.text = "Сначала сохраните организацию, затем добавьте файлы."
                                infoMessageDialog.open()
                            }
                        }
                    }
                }
            }
        }

        // --- Сообщение об ошибке ---
        Label {
            id: errorMessageLabel
            Layout.fillWidth: true
            padding: 10
            leftPadding: 20
            color: "#e74c3c"
            wrapMode: Text.WordWrap
            visible: text !== ""
        }

        // --- Разделитель ---
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#dee2e6"
        }

        // --- Кнопки ---
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "#f8f9fa"

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                spacing: 12

                // --- Кнопка Отмена ---
                Rectangle {
                    width: 100
                    height: 36
                    radius: 8
                    color: {
                        if (cancelBtn.pressed) return "#b0b0b0"
                        if (cancelBtn.hovered) return "#d0d0d0"
                        return "#bdc3c7"
                    }
                    Behavior on color { ColorAnimation { duration: 150 } }
                    MouseArea {
                        id: cancelBtn
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: organizationEditorDialog.close()
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "❌ Отмена"
                        color: "#2c3e50"
                        font.pixelSize: 13
                        font.bold: true
                    }
                }

                // --- Кнопка Сохранить ---
                Rectangle {
                    width: 130
                    height: 36
                    radius: 8
                    color: {
                        if (saveBtn.pressed) return "#1a6e32"
                        if (saveBtn.hovered) return "#27ae60"
                        return "#2ecc71"
                    }
                    Behavior on color { ColorAnimation { duration: 150 } }
                    MouseArea {
                        id: saveBtn
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            errorMessageLabel.text = ""

                            if (!nameField.text.trim()) {
                                errorMessageLabel.text = "Пожалуйста, заполните название организации."
                                return
                            }

                            var orgData = {
                                "name": nameField.text.trim(),
                                "phone": phoneField.text.trim(),
                                "contact_person": contactPersonField.text.trim(),
                                "notes": notesArea.text.trim()
                            }

                            var result
                            if (organizationEditorDialog.isEditMode && organizationEditorDialog.currentOrganizationId > 0) {
                                result = appData.updateOrganization(organizationEditorDialog.currentOrganizationId, orgData)
                                if (result) {
                                    organizationEditorDialog.organizationSaved()
                                    organizationEditorDialog.close()
                                } else {
                                    errorMessageLabel.text = "Ошибка при сохранении. Проверьте логи."
                                }
                            } else {
                                var newId = appData.createOrganization(orgData)
                                if (newId && newId > 0) {
                                    organizationEditorDialog.currentOrganizationId = newId
                                    organizationEditorDialog.isEditMode = true
                                    dialogTitleLabel.text = "Редактировать организацию"
                                    organizationEditorDialog.organizationSaved()
                                    loadReferenceFiles()
                                } else {
                                    errorMessageLabel.text = "Ошибка при сохранении. Проверьте логи."
                                }
                            }
                        }
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "💾 Сохранить"
                        color: "#ffffff"
                        font.pixelSize: 13
                        font.bold: true
                    }
                }
            }
        }
    }

    // --- Диалог информации ---
    Dialog {
        id: infoMessageDialog
        title: "Информация"
        standardButtons: Dialog.Ok
        modal: true
        property string text: ""
        Label { text: infoMessageDialog.text; wrapMode: Text.WordWrap }
    }

    // --- FileDialog ---
    FileDialog {
        id: referenceFileDialog
        title: "Выберите файл справочного материала"
        fileMode: FileDialog.OpenFile
        onAccepted: {
            var selectedFile = referenceFileDialog.selectedFile
            if (selectedFile) {
                var localPath = selectedFile.toString().replace(/^file:[\/\\]{2,3}/, "")
                var fileType = "other"
                var lowerPath = localPath.toLowerCase()
                // Текстовые редакторы (документы)
                if (lowerPath.endsWith(".txt") || lowerPath.endsWith(".doc") || lowerPath.endsWith(".docx") ||
                    lowerPath.endsWith(".odt") || lowerPath.endsWith(".rtf") || lowerPath.endsWith(".pdf") ||
                    lowerPath.endsWith(".pages")) {
                    fileType = "word"
                // Табличные редакторы
                } else if (lowerPath.endsWith(".xls") || lowerPath.endsWith(".xlsx") ||
                           lowerPath.endsWith(".ods") || lowerPath.endsWith(".csv") ||
                           lowerPath.endsWith(".numbers")) {
                    fileType = "excel"
                // Изображения
                } else if (lowerPath.endsWith(".jpg") || lowerPath.endsWith(".jpeg") ||
                           lowerPath.endsWith(".png") || lowerPath.endsWith(".gif") ||
                           lowerPath.endsWith(".bmp") || lowerPath.endsWith(".tiff") ||
                           lowerPath.endsWith(".tif") || lowerPath.endsWith(".webp") ||
                           lowerPath.endsWith(".svg") || lowerPath.endsWith(".raw")) {
                    fileType = "image"
                }
                appData.addOrganizationReferenceFile(organizationEditorDialog.currentOrganizationId, localPath, fileType)
                loadReferenceFiles()
            }
        }
    }

    // --- Диалог удаления файла ---
    Dialog {
        id: fileDeleteConfirmationDialog
        title: "Подтверждение удаления файла"
        standardButtons: Dialog.Yes | Dialog.No
        modal: true
        property int fileIdToDelete: -1
        property string filePathToDelete: ""

        ColumnLayout {
            spacing: 10
            Label {
                text: "Вы действительно хотите удалить файл с диска?"
                font.bold: true
            }
            Label {
                text: fileDeleteConfirmationDialog.filePathToDelete
                font.pixelSize: 12
                color: "#666"
                wrapMode: Text.Wrap
            }
            Label {
                text: "Файл будет удалён безвозвратно!"
                font.pixelSize: 12
                color: "#e74c3c"
            }
        }

        onAccepted: {
            if (fileIdToDelete > 0) {
                var success = appData.deleteOrganizationReferenceFileWithPhysicalFile(fileIdToDelete)
                if (success) {
                    console.log("QML: Файл успешно удалён с диска.")
                }
                loadReferenceFiles()
            }
        }
    }

    // --- Функции ---
    function resetForAdd() {
        isEditMode = false
        currentOrganizationId = -1
        nameField.text = ""
        phoneField.text = ""
        contactPersonField.text = ""
        notesArea.text = ""
        errorMessageLabel.text = ""
        dialogTitleLabel.text = "Добавить организацию"
        referenceFilesListModel.clear()
    }

    function loadDataForEdit(orgData) {
        isEditMode = true
        currentOrganizationId = orgData.id || -1
        nameField.text = orgData.name || ""
        phoneField.text = orgData.phone || ""
        contactPersonField.text = orgData.contact_person || ""
        notesArea.text = orgData.notes || ""
        errorMessageLabel.text = ""
        dialogTitleLabel.text = "Редактировать сведения об организации"
        loadReferenceFiles()
    }

    function loadReferenceFiles() {
        referenceFilesListModel.clear()
        if (currentOrganizationId > 0) {
            var files = appData.getOrganizationReferenceFiles(currentOrganizationId)
            if (files && files.length > 0) {
                for (var i = 0; i < files.length; i++) {
                    referenceFilesListModel.append(files[i])
                }
            }
        }
    }

    onOpened: {
        errorMessageLabel.text = ""
        nameField.forceActiveFocus()
    }
}
