#include "emainmenu.h"

#include "ebutton.h"
#include "eframedbutton.h"

#include "eframedwidget.h"
#include "enamewidget.h"
#include "elanguage.h"
#include "emainwindow.h"
#include "engine/eworldcity.h"

#include <vector>

void addButton(const std::string& text,
               const eAction& a,
               eWidget* const buttons,
               eMainWindow* const window) {
    const auto b1 = new eFramedButton(window);
    b1->setRenderBg(true);
    b1->setUnderline(false);
    buttons->addWidget(b1);
    b1->setPressAction(a);
    b1->setText(text);
    b1->fitContent();
    b1->padToTouchTarget();
    b1->align(eAlignment::hcenter);
}

#ifdef __ANDROID__
// A horizontal dock along the bottom edge: the key art then owns the
// screen, and the four entries become thumb-sized targets instead of a
// narrow column of text in the middle of a very wide display.
static void buildTouchMenu(eMainMenu* const menu,
                           eMainWindow* const w,
                           const eResolution& res,
                           const eAction& newGameA,
                           const eAction& loadGameA,
                           const eAction& settingsA,
                           const eAction& quitA) {
    const int p = res.hugePadding();
    const int buttonH = res.touchTargetMin();

    const auto dock = new eFramedWidget(w);
    dock->setType(eFrameType::message);
    dock->resize(menu->width() - 2*p, buttonH + 2*p);
    menu->addWidget(dock);
    dock->align(eAlignment::hcenter);
    dock->setY(menu->height() - dock->height() - p);

    const auto inner = new eWidget(w);
    inner->setNoPadding();
    inner->resize(dock->width() - 2*p, buttonH);
    dock->addWidget(inner);
    inner->align(eAlignment::center);

    struct eEntry {
        std::string fText;
        eAction fAction;
        double fWidth;
        bool fPrimary;
    };
    const std::vector<eEntry> entries{
        {eLanguage::zeusText(1, 1), newGameA, 0.34, true},
        {eLanguage::zeusText(1, 3), loadGameA, 0.24, false},
        {eLanguage::zeusText(2, 0), settingsA, 0.24, false},
        {eLanguage::zeusText(1, 5), quitA, 0.18, false},
    };

    for(const auto& e : entries) {
        const auto b = new eFramedButton(w);
        b->setRenderBg(e.fPrimary);
        b->setUnderline(true);
        b->setNoPadding();
        b->setText(e.fText);
        b->setFontSize(res.touchFontSize(e.fPrimary ? res.hugeFontSize() :
                                                      res.largeFontSize()));
        b->resize(inner->width()*e.fWidth, buttonH);
        b->setPressAction(e.fAction);
        inner->addWidget(b);
    }
    inner->layoutHorizontally();
}
#endif

void eMainMenu::initialize(const eAction& newGameA,
                           const eAction& loadGameA,
                           const eAction& editGameA,
                           const eAction& settingsA,
                           const eAction& quitA,
                           const eAction& leaderA) {
    eMainMenuBase::initialize();

    const auto w = window();

#ifdef __ANDROID__
    (void)editGameA;
    buildTouchMenu(this, w, resolution(), newGameA, loadGameA,
                   settingsA, quitA);
    {
        const auto leader = new eFramedButton(w);
        leader->setRenderBg(true);
        leader->setUnderline(false);
        leader->setPressAction(leaderA);
        leader->setText(w->leader());
        leader->fitContent();
        leader->padToTouchTarget();
        addWidget(leader);
        const int p = resolution().hugePadding();
        leader->move(p, p);
    }
    return;
#endif

    const auto buttons = new eWidget(w);
    addWidget(buttons);

    const auto res = resolution();
    const int cww = res.centralWidgetLargeWidth();
    const int cwh = res.centralWidgetLargeHeight();
    buttons->resize(cww, cwh);

    buttons->align(eAlignment::center);

    addButton(eLanguage::zeusText(1, 1), newGameA, buttons, w);
    addButton(eLanguage::zeusText(1, 3), loadGameA, buttons, w);
#ifndef __ANDROID__
    // The adventure editor is a mouse-and-keyboard tool; it has no
    // usable touch equivalent.
    addButton(eLanguage::zeusText(287, 3), editGameA, buttons, w);
#else
    (void)editGameA;
#endif
    addButton(eLanguage::zeusText(2, 0), settingsA, buttons, w);
    addButton(eLanguage::zeusText(1, 5), quitA, buttons, w);

    buttons->layoutVertically();

    const auto leader = new eFramedButton(w);
    leader->setRenderBg(true);
    leader->setUnderline(false);
    leader->setPressAction(leaderA);
    leader->setText(w->leader());
    leader->fitContent();
    addWidget(leader);
    const int p = res.hugePadding();
    int tw;
    int th;
    textureSize(tw, th);
    leader->setX((width() - tw)/2 + 2*p);
    leader->setY(2*p);
}

bool eMainMenu::mousePressEvent(const eMouseEvent& e) {
    (void)e;
    mPressed = true;
    return true;
}

bool eMainMenu::mouseReleaseEvent(const eMouseEvent& e) {
    (void)e;
    mPressed = false;
    return true;
}

bool eMainMenu::mouseMoveEvent(const eMouseEvent& e) {
    (void)e;
    return true;
}

bool eMainMenu::mouseEnterEvent(const eMouseEvent& e) {
    (void)e;
    mHover = true;
    return true;
}

bool eMainMenu::mouseLeaveEvent(const eMouseEvent& e) {
    (void)e;
    mHover = false;
    return true;
}
