// ui/main.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Window 6.5

ApplicationWindow {
    id: window
    width: 1200
    height: 900
    minimumWidth: 1000
    minimumHeight: 700
    visible: true
    title: "ВПО «Алгоритм-ДЧ»"

    // --- Свойства для управления состоянием ---
    // true - показывать LoginView, false - показывать MainWindowContent
    property bool showLoginScreen: true

    // --- Login View ---
    LoginView {
        id: loginView
        anchors.fill: parent
        visible: window.showLoginScreen
        // Передаем ссылки на менеджеры (они будут установлены из Python)
        // sqliteConfigManager: null // Будет установлено из Python
        // pgDatabaseManager: null   // Будет установлено из Python
    }

    // --- Main Application Content ---
    MainWindowContent {
        id: mainContent
        anchors.fill: parent
        visible: !window.showLoginScreen
    }

    // --- Функция для переключения на основной экран (вызывается из Python) ---
    function switchToMainScreen() {
        console.log("QML main.qml: switchToMainScreen() вызвана.");
        window.showLoginScreen = false; // Переключаем свойство
        console.log("QML main.qml: showLoginScreen установлено в false.");
        // Можно также вызвать метод onShown для mainContent, если он нужен
        // mainContent.onShown(); // Если такой метод есть
    }

    // --- Функция для переключения на экран входа (вызывается из Python) ---
    function switchToLoginScreen() {
        console.log("QML main.qml: switchToLoginScreen() вызвана.");
        window.showLoginScreen = true; // Переключаем свойство
        console.log("QML main.qml: showLoginScreen установлено в true.");
        // Вызываем метод onShown у LoginView для сброса состояния
        if (loginView.onShown) { // Проверяем, существует ли метод
             loginView.onShown();
        } else {
             console.log("QML main.qml: Метод onShown не найден в LoginView.");
        }
    }
}
