from pathlib import Path


def main() -> None:
    source = Path(
        "HVAC/gui_v3/widgets/"
        "construction_layer_path_schematic_widget_v1.py"
    ).read_text(encoding="utf-8")

    assert "painter.setRenderHint(QPainter.Antialiasing)" in source
    assert "colour.setAlpha(220)" in source
    assert "pen.setWidthF(2.5 if path_index == 0 else 2.0)" in source
    assert "pen.setCapStyle(Qt.PenCapStyle.RoundCap)" in source
    assert "pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)" in source
    assert "legend_pen.setCapStyle(Qt.PenCapStyle.RoundCap)" in source
    assert "QPen(colour, 3 if path_index == 0 else 2)" not in source

    # Thermal evidence remains piecewise-linear: no spline/curve interpolation.
    assert "painter.drawLine(previous, here)" in source
    assert "drawCubic" not in source
    assert "cubicTo" not in source

    print(
        "OK — U-S5F1G temperature paths use softened anti-aliased strokes "
        "without changing their straight calculated segments."
    )


if __name__ == "__main__":
    main()
