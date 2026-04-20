// ui/LoginView.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Item {
    id: loginViewRoot
    // signal loginSuccessful() // Сигнал для уведомления об успешном входе

    // Свойства для передачи менеджеров из main.py
    property var sqliteConfigManager: null
    property var pgDatabaseManager: null

    // --- Основной столбец для размещения элементов ---
    ColumnLayout {
        anchors.centerIn: parent
        spacing: 20
        width: 300

        // Заголовок
        Label {
            text: "Вход в ВПО «Алгоритм-ДЧ»"
            font.pointSize: 16
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
        }

        // Поле ввода логина
        Label {
            text: "Логин:"
        }
        TextField {
            id: loginField
            Layout.fillWidth: true
            placeholderText: "Введите логин..."
            // selectAll() и forceActiveFocus() можно вызвать из Python при показе окна
        }

        // Поле ввода пароля
        Label {
            text: "Пароль:"
        }
        TextField {
            id: passwordField
            Layout.fillWidth: true
            placeholderText: "Введите пароль..."
            echoMode: TextInput.Password
            // Нажатие Enter в поле пароля тоже может вызывать вход
            onAccepted: loginButton.clicked()
        }

        // Сообщение об ошибке (изначально скрыто)
        Label {
            id: errorLabel
            text: ""
            color: "red"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            visible: text !== ""
        }

        // Кнопки
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Button {
                id: loginButton
                text: "Войти"
                Layout.fillWidth: true
                onClicked: {
                    var login = loginField.text.trim()
                    var password = passwordField.text

                    if (login === "" || password === "") {
                        errorLabel.text = "Пожалуйста, заполните все поля."
                        return
                    }

                    console.log("QML: Попытка входа для пользователя:", login)
                    errorLabel.text = "" // Очищаем предыдущую ошибку

                    // Вызываем метод из main.py для проверки учетных данных
                    // appData.authenticateAndLogin - это слот, который мы создали
                    var loginResult = appData.authenticateAndLogin(login, password)

                    if (typeof loginResult === 'boolean' && loginResult) {
                        console.log("QML: Вход успешен для", login)
                        // Здесь мы должны сообщить main.py, что вход успешен,
                        // и он должен переключить экран на основной.
                        // Пока просто выведем сообщение.
                        errorLabel.text = "Вход успешен! Переход..."
                        errorLabel.color = "green"
                        // Очищаем поля
                        loginField.text = ""
                        passwordField.text = ""
                        // TODO: Вызов функции/сигнала для перехода на MainWindow

                    } else if (typeof loginResult === 'string') {
                        // Предполагаем, что строка - это сообщение об ошибке
                        console.log("QML: Ошибка входа:", loginResult)
                        errorLabel.text = loginResult
                        errorLabel.color = "red"
                    } else {
                        console.log("QML: Неизвестная ошибка входа.")
                        errorLabel.text = "Ошибка аутентификации. Попробуйте еще раз."
                        errorLabel.color = "red"
                    }
                }
            }

            // --- Кнопка для выхода из приложения ---
            Button {
                id: exitAppButton
                text: "Выход из приложения"
                Layout.fillWidth: true
                onClicked: {
                    console.log("QML LoginView: Кнопка 'Выход из приложения' нажата.");
                    // Вызываем метод из Python для выхода из приложения
                    appData.quitApp();
                }
            }
            // --- ---
        }
    }

    // Обработчик, вызываемый из Python при показе окна
    function onShown() {
        // Очищаем поля и фокусируемся на логине
        loginField.text = ""
        passwordField.text = ""
        errorLabel.text = ""
        loginField.forceActiveFocus()
        console.log("QML LoginView: Окно показано и готово к вводу.")
    }
}