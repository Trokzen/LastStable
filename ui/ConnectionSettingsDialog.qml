// ui/ConnectionSettingsDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Popup {
    id: connectionSettingsDialog
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    width: Math.min(parent.width * 0.6, 500) // 60% ширины или максимум 500
    height: Math.min(parent.height * 0.65, 450) // Увеличена высота для нового поля
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    // --- Свойства для временного хранения настроек ---
    property string tempHost: ""
    property string tempPort: "5432"
    property string tempDbName: ""
    property string tempUser: ""
    property string tempPassword: "" // Для нового пароля

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
            text: "Настройки подключения к БД PostgreSQL"
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
                text: "Хост:"
                Layout.alignment: Qt.AlignRight
            }
            TextField {
                id: hostField
                Layout.fillWidth: true
                placeholderText: "localhost"
                text: connectionSettingsDialog.tempHost
                onTextChanged: connectionSettingsDialog.tempHost = text
            }

            Label {
                text: "Порт:"
                Layout.alignment: Qt.AlignRight
            }
            TextField {
                id: portField
                Layout.fillWidth: true
                placeholderText: "5432"
                text: connectionSettingsDialog.tempPort
                validator: IntValidator { bottom: 1; top: 65535 }
                onTextChanged: connectionSettingsDialog.tempPort = text
            }

            Label {
                text: "Имя БД:"
                Layout.alignment: Qt.AlignRight
            }
            TextField {
                id: dbNameField
                Layout.fillWidth: true
                placeholderText: "algodch_db"
                text: connectionSettingsDialog.tempDbName
                onTextChanged: connectionSettingsDialog.tempDbName = text
            }

            Label {
                text: "Пользователь:"
                Layout.alignment: Qt.AlignRight
            }
            TextField {
                id: userField
                Layout.fillWidth: true
                placeholderText: "algodch_user"
                text: connectionSettingsDialog.tempUser
                onTextChanged: connectionSettingsDialog.tempUser = text
            }

            // --- НОВОЕ: Поле для ввода НОВОГО пароля ---
            Label {
                text: "Новый пароль\n(если меняется):"
                Layout.alignment: Qt.AlignRight | Qt.AlignTop
                ToolTip.text: "Оставьте пустым, чтобы сохранить текущий пароль."
                ToolTip.visible: hovered
            }
            TextField {
                id: newPasswordField
                Layout.fillWidth: true
                placeholderText: "Введите новый пароль..."
                echoMode: TextInput.Password // Маскируем ввод
                onTextChanged: connectionSettingsDialog.tempPassword = text
            }
            // --- ---
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
            Item {
                Layout.fillWidth: true // Заполнитель слева
            }
            Button {
                text: "Отмена"
                onClicked: {
                    console.log("QML ConnectionSettings: Нажата кнопка Отмена");
                    connectionSettingsDialog.close(); // Просто закрываем
                }
            }
            Button {
                text: "Сохранить"
                onClicked: {
                    console.log("QML ConnectionSettings: Нажата кнопка Сохранить");
                    errorMessageLabel.text = ""; // Очищаем предыдущие ошибки

                    // Базовая валидация
                    if (!connectionSettingsDialog.tempHost || !connectionSettingsDialog.tempDbName || !connectionSettingsDialog.tempUser) {
                        errorMessageLabel.text = "Пожалуйста, заполните все обязательные поля.";
                        return;
                    }
                    var portInt = parseInt(connectionSettingsDialog.tempPort, 10);
                    if (isNaN(portInt) || portInt < 1 || portInt > 65535) {
                         errorMessageLabel.text = "Порт должен быть целым числом от 1 до 65535.";
                         return;
                    }

                    // Подготавливаем объект настроек для отправки в Python
                    var newConfig = {
                        "host": connectionSettingsDialog.tempHost,
                        "port": connectionSettingsDialog.tempPort,
                        "dbname": connectionSettingsDialog.tempDbName,
                        "user": connectionSettingsDialog.tempUser,
                        // --- Отправляем НОВЫЙ пароль ---
                        "new_password": connectionSettingsDialog.tempPassword
                        // --- ---
                    };
                    console.log("QML ConnectionSettings: Отправляем новые настройки (включая новый пароль) в Python:", JSON.stringify(newConfig));

                    // Вызываем метод Python для сохранения
                    var resultMessage = appData.savePgConnectionConfig(newConfig);
                    if (resultMessage === true || resultMessage === "") {
                        console.log("QML ConnectionSettings: Настройки успешно сохранены в local_config.db.");
                        connectionSettingsDialog.close(); // Закрываем диалог
                    } else {
                        errorMessageLabel.text = resultMessage; // Отображаем сообщение об ошибке
                        console.warn("QML ConnectionSettings: Ошибка при сохранении настроек:", resultMessage);
                    }
                }
            }
        }
    }

    // --- Функция для загрузки текущих настроек из Python ---
    function loadSettingsFromPython() {
        console.log("QML ConnectionSettings: Запрос текущих настроек подключения у Python...");
        var configFromPython = appData.getPgConnectionConfig();
        console.log("QML ConnectionSettings: Получены настройки из Python:", JSON.stringify(configFromPython));

        if (configFromPython && typeof configFromPython === 'object') {
            connectionSettingsDialog.tempHost = configFromPython.host || "";
            connectionSettingsDialog.tempPort = String(configFromPython.port || "5432");
            connectionSettingsDialog.tempDbName = configFromPython.dbname || "";
            connectionSettingsDialog.tempUser = configFromPython.user || "";
            // connectionSettingsDialog.tempPassword = ""; // НЕ загружаем пароль

            hostField.text = connectionSettingsDialog.tempHost;
            portField.text = connectionSettingsDialog.tempPort;
            dbNameField.text = connectionSettingsDialog.tempDbName;
            userField.text = connectionSettingsDialog.tempUser;
            
            // --- ВАЖНО: Очищаем поле нового пароля при загрузке ---
            newPasswordField.text = "";
            connectionSettingsDialog.tempPassword = "";
            // --- ---
            
            console.log("QML ConnectionSettings: Настройки загружены в диалог.");
        } else {
            console.warn("QML ConnectionSettings: Не удалось получить корректные настройки из Python.");
            // Оставляем поля пустыми или с дефолтными значениями
            connectionSettingsDialog.tempHost = "";
            connectionSettingsDialog.tempPort = "5432";
            connectionSettingsDialog.tempDbName = "";
            connectionSettingsDialog.tempUser = "";
            newPasswordField.text = ""; // Убедиться, что поле пароля пустое
            connectionSettingsDialog.tempPassword = "";
        }
    }
    // --- ---

    // --- Обработчик открытия диалога ---
    onOpened: {
        console.log("QML ConnectionSettings: Диалог открыт. Загружаем настройки...");
        connectionSettingsDialog.loadSettingsFromPython();
        errorMessageLabel.text = ""; // Очищаем сообщения об ошибках
    }
    // --- ---
}