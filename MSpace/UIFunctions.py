def layout_widgets(layout):
    return (layout.itemAt(i).widget() for i in range(layout.count()))
