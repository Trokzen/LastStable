# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

filepath = 'd:/Projects/VPO/DuOfficer_SQLite/Qwen_DuOfficer/ui/SettingsView.qml'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Old button 1: Добавить
old1 = 'Button {\n                            text: "Добавить"'
new1 = 'Rectangle {\n                            Layout.preferredWidth: 110\n                            Layout.preferredHeight: 36\n                            radius: 8\n                            color: {\n                                if (addOfficerBtn.pressed) return "#218c3d"\n                                if (addOfficerBtn.hovered) return "#2ecc71"\n                                return "#27ae60"\n                            }\n                            Behavior on color { ColorAnimation { duration: 150 } }\n                            MouseArea {\n                                id: addOfficerBtn\n                                anchors.fill: parent\n                                hoverEnabled: true\n                                cursorShape: Qt.PointingHandCursor\n                                onClicked: {\n                                    officerEditorDialog.resetForAdd()\n                                    officerEditorDialog.open()\n                                }\n                            }\n                            Text {\n                                anchors.centerIn: parent\n                                text: "\u2795 Добавить"\n                                color: "#ffffff"\n                                font.pixelSize: 13\n                                font.bold: true\n                            }\n                        }\n                        Button {'

if old1[:30] in content:
    idx = content.find(old1[:30])
    # Find the end of this button block
    end_marker = content.find('}\n                        }\n                        Button {', idx)
    if end_marker > 0:
        end_marker += len('}\n                        }')
        content = content[:idx] + new1 + content[end_marker:]
        print('Replaced Button 1 (Add)')

# Old button 2: Редактировать  
old2_start = 'Button {\n                            text: "Редактировать"'
if old2_start[:20] in content:
    idx = content.find(old2_start[:20])
    end_marker = content.find('}\n                        }\n                        Button {', idx)
    if end_marker > 0:
        end_marker += len('}\n                        }')
        new2 = 'Rectangle {\n                            Layout.preferredWidth: 130\n                            Layout.preferredHeight: 36\n                            radius: 8\n                            color: {\n                                if (editOfficerBtn.pressed) return "#c9951d"\n                                if (editOfficerBtn.hovered) return "#f39c12"\n                                return "#f1c40f"\n                            }\n                            Behavior on color { ColorAnimation { duration: 150 } }\n                            opacity: officersListView.currentIndex !== -1 ? 1.0 : 0.5\n                            MouseArea {\n                                id: editOfficerBtn\n                                anchors.fill: parent\n                                hoverEnabled: true\n                                cursorShape: Qt.PointingHandCursor\n                                enabled: officersListView.currentIndex !== -1\n                                onClicked: {\n                                    var selectedIndex = officersListView.currentIndex\n                                    if (selectedIndex !== -1) {\n                                        var officerData = officersListView.model.get(selectedIndex)\n                                        officerEditorDialog.loadDataForEdit(officerData)\n                                        officerEditorDialog.open()\n                                    }\n                                }\n                            }\n                            Text {\n                                anchors.centerIn: parent\n                                text: "\u270f\ufe0f Редактировать"\n                                color: "#2c3e50"\n                                font.pixelSize: 13\n                                font.bold: true\n                            }\n                        }\n                        Button {'
        content = content[:idx] + new2 + content[end_marker:]
        print('Replaced Button 2 (Edit)')

# Old button 3: Удалить
old3_start = 'Button {\n                            text: "Удалить"'
if old3_start[:20] in content:
    idx = content.find(old3_start[:20])
    end_marker = content.find('}\n                        }\n                        // Заполнитель', idx)
    if end_marker > 0:
        end_marker += len('}\n                        }')
        new3 = 'Rectangle {\n                            Layout.preferredWidth: 110\n                            Layout.preferredHeight: 36\n                            radius: 8\n                            color: {\n                                if (delOfficerBtn.pressed) return "#c0392b"\n                                if (delOfficerBtn.hovered) return "#e74c3c"\n                                return "#e8453c"\n                            }\n                            Behavior on color { ColorAnimation { duration: 150 } }\n                            opacity: officersListView.currentIndex !== -1 ? 1.0 : 0.5\n                            MouseArea {\n                                id: delOfficerBtn\n                                anchors.fill: parent\n                                hoverEnabled: true\n                                cursorShape: Qt.PointingHandCursor\n                                enabled: officersListView.currentIndex !== -1\n                                onClicked: {\n                                    var selectedIndex = officersListView.currentIndex\n                                    if (selectedIndex !== -1) {\n                                        var officerData = officersListView.model.get(selectedIndex)\n                                        var result = appData.deleteDutyOfficer(officerData.id)\n                                        if (result === true || (typeof result === \'number\' && result > 0)) {\n                                            settingsViewRoot.loadDutyOfficers()\n                                        }\n                                    }\n                                }\n                            }\n                            Text {\n                                anchors.centerIn: parent\n                                text: "\U0001f5d1\ufe0f Удалить"\n                                color: "#ffffff"\n                                font.pixelSize: 13\n                                font.bold: true\n                            }\n                        }\n                        // Заполнитель'
        content = content[:idx] + new3 + content[end_marker:]
        print('Replaced Button 3 (Delete)')

# Old button 4: Обновить
old4_start = 'Button {\n                            text: "Обновить"'
if old4_start[:20] in content:
    idx = content.find(old4_start[:20])
    end_marker = content.find('}\n                        }\n                    }', idx)
    if end_marker > 0:
        end_marker += len('}\n                        }')
        new4 = 'Rectangle {\n                            Layout.preferredWidth: 110\n                            Layout.preferredHeight: 36\n                            radius: 8\n                            color: {\n                                if (refreshOfficerBtn.pressed) return "#2980b9"\n                                if (refreshOfficerBtn.hovered) return "#3498db"\n                                return "#5dade2"\n                            }\n                            Behavior on color { ColorAnimation { duration: 150 } }\n                            MouseArea {\n                                id: refreshOfficerBtn\n                                anchors.fill: parent\n                                hoverEnabled: true\n                                cursorShape: Qt.PointingHandCursor\n                                onClicked: settingsViewRoot.loadDutyOfficers()\n                            }\n                            Text {\n                                anchors.centerIn: parent\n                                text: "\U0001f504 Обновить"\n                                color: "#ffffff"\n                                font.pixelSize: 13\n                                font.bold: true\n                            }\n                        }\n                    }'
        content = content[:idx] + new4 + content[end_marker:]
        print('Replaced Button 4 (Refresh)')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! All 4 buttons replaced.')
