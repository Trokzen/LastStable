// ui/OrganizationsListView.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Item {
    id: organizationsListViewRoot
    
    // --- Свойства ---
    property int currentIndex: -1
    property var organizationDataList: [] // Кэш данных для быстрого доступа

    // --- Функция для получения данных организации по индексу ---
    function getOrganizationData(index) {
        if (index >= 0 && index < organizationDataList.length) {
            return organizationDataList[index]
        }
        return null
    }

    // --- Функция загрузки списка организаций ---
    function loadOrganizations() {
        console.log("QML OrganizationsListView: === НАЧАЛО ЗАГРУЗКИ ===")
        var orgs = appData.getAllOrganizations()
        console.log("QML OrganizationsListView: Получено от appData:", orgs)
        console.log("QML OrganizationsListView: orgs.length:", orgs ? orgs.length : "N/A")
        console.log("QML OrganizationsListView: orgs.hasOwnProperty('length'):", orgs ? orgs.hasOwnProperty('length') : "N/A")
        
        organizationDataList = []
        organizationsListModel.clear()
        
        // Qt 6: Array.isArray может возвращать false для списков из Python
        // Проверяем по длине или по наличию свойства length
        if (orgs && orgs.length !== undefined) {
            for (var i = 0; i < orgs.length; i++) {
                var org = orgs[i]
                console.log("QML OrganizationsListView: org[", i, "] =", org)
                organizationsListModel.append({
                    "id": org.id || -1,
                    "name": org.name || "",
                    "phone": org.phone || "",
                    "contact_person": org.contact_person || "",
                    "notes": org.notes || ""
                })
                organizationDataList.push(org)
            }
            console.log("QML OrganizationsListView: Загружено", organizationsListModel.count, "организаций.")
        } else {
            console.log("QML OrganizationsListView: orgs пуст или не имеет свойства length!")
        }
        currentIndex = -1
    }

    // --- События (сигналы) ---
    signal organizationSelected(var orgData)
    signal organizationDoubleClicked(var orgData)

    // --- Инициализация при создании ---
    Component.onCompleted: {
        loadOrganizations()
    }

    // --- Обработка изменения видимости ---
    onVisibleChanged: {
        if (visible) {
            loadOrganizations()
        }
    }

    // --- ScrollView + ListView ---
    ScrollView {
        anchors.fill: parent
        clip: true

        ListView {
            id: organizationsListView
            width: Math.max(parent.width, organizationsListViewRoot.width)
            model: ListModel { id: organizationsListModel }
            delegate: Rectangle {
                width: ListView.view.width
                height: 50
                color: {
                    if (organizationsListView.currentIndex === index) {
                        return "#d5e8f7" // Голубой для выбранного
                    }
                    return index % 2 ? "#f9f9f9" : "#ffffff" // Чередующийся фон
                }
                border.color: organizationsListView.currentIndex === index ? "#3498db" : "#ddd"
                border.width: organizationsListView.currentIndex === index ? 2 : 1
                radius: 3

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 10

                    // Название организации
                    Text {
                        Layout.fillWidth: true
                        text: "<b>" + (model.name || "Без названия") + "</b>"
                        font.pixelSize: 14
                        elide: Text.ElideRight
                    }

                    // Телефон
                    Text {
                        Layout.preferredWidth: 150
                        text: model.phone || "—"
                        font.pixelSize: 13
                        color: "#666"
                        elide: Text.ElideRight
                        horizontalAlignment: Text.AlignRight
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        organizationsListView.currentIndex = index
                        organizationsListViewRoot.currentIndex = index
                        var orgData = organizationsListViewRoot.getOrganizationData(index)
                        if (orgData) {
                            organizationsListViewRoot.organizationSelected(orgData)
                        }
                    }
                    onDoubleClicked: {
                        organizationsListView.currentIndex = index
                        organizationsListViewRoot.currentIndex = index
                        var orgData = organizationsListViewRoot.getOrganizationData(index)
                        if (orgData) {
                            organizationsListViewRoot.organizationDoubleClicked(orgData)
                        }
                    }
                }
            }

            // --- Сообщение, если список пуст ---
            Label {
                anchors.centerIn: parent
                text: "Нет организаций. Нажмите 'Добавить' для создания."
                color: "gray"
                font.pixelSize: 14
                visible: organizationsListModel.count === 0
            }
        }
    }
}
