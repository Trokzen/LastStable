// ui/algorithms/ExecutionStatsChartDialog.qml
import QtQuick 6.5
import QtQuick.Controls 6.5
import QtCharts 6.5

Dialog {
    id: chartDialog
    title: "Статистика выполнения действий"
    width: 550
    height: 450
    modal: true
    standardButtons: Dialog.Close

    property var stats: ({ on_time: 0, late: 0, not_done: 0, total: 0 })

    ChartView {
        anchors.fill: parent
        anchors.margins: 20
        legend.visible: true
        legend.alignment: Qt.AlignRight

        PieSeries {
            id: pieSeries
            size: 0.7  // 70% от доступного пространства

            Component.onCompleted: {
                // Очищаем старые срезы
                while (count > 0) remove(0);

                if (stats.on_time > 0) {
                    var s1 = append("Своевременно", stats.on_time);
                    s1.color = "#4CAF50";
                }
                if (stats.late > 0) {
                    var s2 = append("Несвоевременно", stats.late);
                    s2.color = "#FF9800";
                }
                if (stats.not_done > 0) {
                    var s3 = append("Не выполнено", stats.not_done);
                    s3.color = "#9E9E9E";
                }
                if (stats.total === 0) {
                    var s0 = append("Нет данных", 1);
                    s0.color = "#BDBDBD";
                }

                // Добавляем проценты на срезы
                for (var i = 0; i < count; i++) {
                    var slice = at(i);
                    var pct = Math.round(slice.value / stats.total * 100);
                    slice.label = `${slice.label} (${pct}%)`;
                    slice.labelVisible = true;
                    slice.labelColor = "white";
                    slice.labelFont.pixelSize = 13;
                    slice.labelFont.bold = true;
                }
            }

            // Опционально: эффект "выталкивания" при наведении
            onHovered: function(slice, state) {
                slice.explodeDistanceFactor = state ? 0.1 : 0;
            }
        }
    }
}