#ifndef ESCROLLWIDGET_H
#define ESCROLLWIDGET_H

#include "ewidget.h"

class eScrollWidget : public eWidget {
public:
    using eWidget::eWidget;

    void initializeButtons();

    void setScrollArea(eWidget* const w);
    eWidget* scrollArea() const { return mScrollArea; }

    void scrollUp();
    void scrollDown();
    void scrollToTheTop();
    void clampDY();

    void renderTargetsReset() override;
protected:
    void paintEvent(ePainter& p) override;

    bool keyPressEvent(const eKeyPressEvent& e) override;
    bool mouseWheelEvent(const eMouseWheelEvent& e) override;
    // Dragging the list itself — the only scroll gesture a phone has,
    // since there is no wheel and the arrow buttons are tiny.
    bool mousePressEvent(const eMouseEvent& e) override;
    bool mouseMoveEvent(const eMouseEvent& e) override;
    bool mouseReleaseEvent(const eMouseEvent& e) override;
private:
    int mDy = 0;

    bool mDragging = false;
    int mDragStartY = 0;
    int mDyAtDragStart = 0;

    eWidget* mScrollArea = nullptr;
    eWidget* mUpButton = nullptr;
    eWidget* mDownButton = nullptr;
};

#endif // ESCROLLWIDGET_H
