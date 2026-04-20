// ui/OfficerEditorDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Popup {
    id: officerEditorDialog
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    width: Math.min(parent.width * 0.5, 400) // 50% ширины или максимум 400
    height: Math.min(parent.height * 0.6, 500) // Увеличена высота для новых полей
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // --- Свойства для передачи/получения данных ---
    property bool isEditMode: false // true - редактирование, false - добавление
    property var officerData: ({})

    // --- Временные свойства для редактирования ---
    property string tempRank: ""
    property string tempLastName: ""
    property string tempFirstName: ""
    property string tempMiddleName: ""
    property string tempPhone: ""
    property bool tempIsActive: true
    property bool tempIsAdmin: false
    // --- НОВОЕ: Свойства для логина и пароля ---
    property string tempLogin: ""
    property string tempPassword: "" // Для нового пароля
    // --- ---

    background: Rectangle {
        color: "white"
        border.color: "lightgray"
        radius: 5
    }

    // --- Основной столбец для элементов диалога ---
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        Label {
            id: dialogTitleLabel
            text: officerEditorDialog.isEditMode ? "Редактировать должностное лицо" : "Добавить новое должностное лицо"
            font.pointSize: 14
            font.bold: true
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            GridLayout {
                id: formGridLayout
                width: parent.width
                columnSpacing: 10
                rowSpacing: 10
                columns: 2

                Label { text: "Звание:"; Layout.alignment: Qt.AlignRight }
                TextField {
                    id: rankField
                    Layout.fillWidth: true
                    placeholderText: "Введите звание..."
                    text: officerEditorDialog.tempRank
                    onTextChanged: officerEditorDialog.tempRank = text
                }

                Label { text: "Фамилия:"; Layout.alignment: Qt.AlignRight }
                TextField {
                    id: lastNameField
                    Layout.fillWidth: true
                    placeholderText: "Введите фамилию..."
                    text: officerEditorDialog.tempLastName
                    onTextChanged: officerEditorDialog.tempLastName = text
                }

                Label { text: "Имя:"; Layout.alignment: Qt.AlignRight }
                TextField {
                    id: firstNameField
                    Layout.fillWidth: true
                    placeholderText: "Введите имя..."
                    text: officerEditorDialog.tempFirstName
                    onTextChanged: officerEditorDialog.tempFirstName = text
                }

                Label { text: "Отчество:"; Layout.alignment: Qt.AlignRight }
                TextField {
                    id: middleNameField
                    Layout.fillWidth: true
                    placeholderText: "Введите отчество..."
                    text: officerEditorDialog.tempMiddleName
                    onTextChanged: officerEditorDialog.tempMiddleName = text
                }

                Label { text: "Телефон:"; Layout.alignment: Qt.AlignRight }
                TextField {
                    id: phoneField
                    Layout.fillWidth: true
                    placeholderText: "Введите номер телефона..."
                    text: officerEditorDialog.tempPhone
                    onTextChanged: officerEditorDialog.tempPhone = text
                }

                // --- НОВОЕ: Поле для логина ---
                Label { text: "Логин:"; Layout.alignment: Qt.AlignRight }
                TextField {
                    id: loginField
                    Layout.fillWidth: true
                    placeholderText: "Введите логин..."
                    text: officerEditorDialog.tempLogin
                    onTextChanged: officerEditorDialog.tempLogin = text
                }
                // --- ---

                // --- НОВОЕ: Поле для пароля ---
                Label {
                    text: officerEditorDialog.isEditMode ? "Новый пароль:" : "Пароль:"
                    Layout.alignment: Qt.AlignRight
                    ToolTip.text: officerEditorDialog.isEditMode ? "Оставьте пустым, чтобы сохранить текущий пароль." : ""
                    ToolTip.visible: hovered && officerEditorDialog.isEditMode
                }
                TextField {
                    id: passwordField
                    Layout.fillWidth: true
                    placeholderText: officerEditorDialog.isEditMode ? "Введите новый пароль..." : "Введите пароль..."
                    echoMode: TextInput.Password // Маскируем ввод
                    text: officerEditorDialog.tempPassword
                    onTextChanged: officerEditorDialog.tempPassword = text
                }
                // --- ---

                Label { text: "Активен:"; Layout.alignment: Qt.AlignRight }
                CheckBox {
                    id: isActiveCheckBox
                    checked: officerEditorDialog.tempIsActive
                    onCheckedChanged: officerEditorDialog.tempIsActive = checked
                }

                Label { text: "Администратор:"; Layout.alignment: Qt.AlignRight }
                CheckBox {
                    id: isAdminCheckBox
                    checked: officerEditorDialog.tempIsAdmin
                    onCheckedChanged: officerEditorDialog.tempIsAdmin = checked
                }
            }
        }

        // --- Сообщения об ошибках ---
        Label {
            id: errorMessageLabel
            Layout.fillWidth: true
            color: "red"
            wrapMode: Text.WordWrap
            visible: text !== ""
        }

        // --- Кнопки ---
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Item { Layout.fillWidth: true } // Заполнитель слева
            Button {
                text: "Отмена"
                onClicked: {
                    console.log("QML OfficerEditor: Нажата кнопка Отмена");
                    officerEditorDialog.close();
                }
            }
            Button {
                id: saveButton
                text: "Сохранить"
                onClicked: {
                    console.log("QML OfficerEditor: Нажата кнопка Сохранить");
                    errorMessageLabel.text = "";

                    // Базовая валидация
                    if (!officerEditorDialog.tempRank || !officerEditorDialog.tempLastName || !officerEditorDialog.tempFirstName) {
                        errorMessageLabel.text = "Звание, фамилия и имя обязательны для заполнения.";
                        return;
                    }
                    // --- ДОБАВИТЬ: Валидация логина ---
                    if (!officerEditorDialog.tempLogin) {
                         errorMessageLabel.text = "Логин обязателен для заполнения.";
                         return;
                    }
                    // --- ---

                    // Подготавливаем данные для отправки в Python
                    var officerDataToSend = {
                        "rank": officerEditorDialog.tempRank,
                        "last_name": officerEditorDialog.tempLastName,
                        "first_name": officerEditorDialog.tempFirstName,
                        "middle_name": officerEditorDialog.tempMiddleName || null,
                        "phone": officerEditorDialog.tempPhone || null,
                        "is_active": officerEditorDialog.tempIsActive ? 1 : 0,
                        "is_admin": officerEditorDialog.tempIsAdmin ? 1 : 0,
                        // --- ДОБАВИТЬ: Логин и пароль ---
                        "login": officerEditorDialog.tempLogin,
                        "new_password": officerEditorDialog.tempPassword || null // Отправляем null, если пусто
                        // --- ---
                    };

                    var result;
                    if (officerEditorDialog.isEditMode) {
                        // --- Режим редактирования ---
                        console.log("QML OfficerEditor: Отправляем обновление пользователя в Python. ID:", officerEditorDialog.officerData.id, "Данные:", JSON.stringify(officerDataToSend));
                        result = appData.updateDutyOfficer(officerEditorDialog.officerData.id, officerDataToSend);
                        // --- ---
                    } else {
                        // --- Режим добавления ---
                        console.log("QML OfficerEditor: Отправляем нового пользователя в Python. Данные:", JSON.stringify(officerDataToSend));
                        result = appData.addDutyOfficer(officerDataToSend);
                        // --- ---
                    }

                    if (typeof result === 'number' && result > 0) {
                        // Успех (для addDutyOfficer возвращается ID, для updateDutyOfficer обычно true или ID)
                        console.log("QML OfficerEditor: Операция с пользователем успешна. Результат:", result);
                        officerEditorDialog.close();
                        // --- Сигнал для уведомления SettingsView о необходимости перезагрузить список ---
                        officerEditorDialog.accepted(); // Эмитируем сигнал accepted
                        // --- ---
                    } else if (result === true) {
                         console.log("QML OfficerEditor: Операция обновления пользователя успешна.");
                         officerEditorDialog.close();
                         officerEditorDialog.accepted(); // Эмитируем сигнал accepted
                    } else if (typeof result === 'string') {
                        // Ошибка
                        errorMessageLabel.text = result;
                        console.warn("QML OfficerEditor: Ошибка операции с пользователем:", result);
                    } else {
                        errorMessageLabel.text = "Неизвестная ошибка при выполнении операции.";
                        console.error("QML OfficerEditor: Неизвестная ошибка операции с пользователем. Результат:", result);
                    }
                }
            }
        }
    }

    // --- Функция для загрузки данных пользователя в диалог (для редактирования) ---
    function loadDataForEdit(data) {
        console.log("QML OfficerEditor: Загрузка данных пользователя для редактирования:", JSON.stringify(data));
        officerEditorDialog.isEditMode = true;
        officerEditorDialog.officerData = data || ({});

        officerEditorDialog.tempRank = data.rank || "";
        officerEditorDialog.tempLastName = data.last_name || "";
        officerEditorDialog.tempFirstName = data.first_name || "";
        officerEditorDialog.tempMiddleName = data.middle_name || "";
        officerEditorDialog.tempPhone = data.phone || "";
        officerEditorDialog.tempIsActive = (data.is_active === 1 || data.is_active === true);
        officerEditorDialog.tempIsAdmin = (data.is_admin === 1 || data.is_admin === true);
        // --- ДОБАВИТЬ: Загрузка логина ---
        officerEditorDialog.tempLogin = data.login || "";
        // --- ---
        // Пароль не загружаем, поле будет пустым для ввода нового

        // Обновляем поля ввода
        rankField.text = officerEditorDialog.tempRank;
        lastNameField.text = officerEditorDialog.tempLastName;
        firstNameField.text = officerEditorDialog.tempFirstName;
        middleNameField.text = officerEditorDialog.tempMiddleName;
        phoneField.text = officerEditorDialog.tempPhone;
        isActiveCheckBox.checked = officerEditorDialog.tempIsActive;
        isAdminCheckBox.checked = officerEditorDialog.tempIsAdmin;
        // --- ДОБАВИТЬ: Обновление поля логина ---
        loginField.text = officerEditorDialog.tempLogin;
        // --- ---
        // Поле пароля оставляем пустым
        passwordField.text = "";
        officerEditorDialog.tempPassword = ""; // Сбрасываем временное значение

        console.log("QML OfficerEditor: Данные пользователя загружены в диалог.");
    }
    // --- ---

    // --- Функция для сброса диалога в режим добавления ---
    function resetForAdd() {
        console.log("QML OfficerEditor: Сброс диалога в режим добавления.");
        officerEditorDialog.isEditMode = false;
        officerEditorDialog.officerData = ({});

        officerEditorDialog.tempRank = "";
        officerEditorDialog.tempLastName = "";
        officerEditorDialog.tempFirstName = "";
        officerEditorDialog.tempMiddleName = "";
        officerEditorDialog.tempPhone = "";
        officerEditorDialog.tempIsActive = true;
        officerEditorDialog.tempIsAdmin = false;
        // --- ДОБАВИТЬ: Сброс логина и пароля ---
        officerEditorDialog.tempLogin = "";
        officerEditorDialog.tempPassword = "";
        // --- ---

        // Обновляем поля ввода
        rankField.text = "";
        lastNameField.text = "";
        firstNameField.text = "";
        middleNameField.text = "";
        phoneField.text = "";
        isActiveCheckBox.checked = true;
        isAdminCheckBox.checked = false;
        // --- ДОБАВИТЬ: Сброс полей логина и пароля ---
        loginField.text = "";
        passwordField.text = "";
        // --- ---
        
        errorMessageLabel.text = "";
        console.log("QML OfficerEditor: Диалог сброшен.");
    }
    // --- ---

    // --- Обработчик открытия диалога ---
    onOpened: {
        console.log("QML OfficerEditor: Диалог открыт.");
        errorMessageLabel.text = "";
        // Фокус на первое поле
        rankField.forceActiveFocus();
    }
    // --- ---

    // --- Сигнал для уведомления об успешном завершении ---
    signal accepted()
    // --- ---
}