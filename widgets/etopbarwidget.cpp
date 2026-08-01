#include "etopbarwidget.h"

#include "engine/egameboard.h"
#include "engine/boardData/epopulationdata.h"
#include "textures/egametextures.h"
#include "ebutton.h"
#include "edatewidget.h"
#include "egamewidget.h"

#include "emainwindow.h"

void eTopBarWidget::initialize() {
    const auto& intrfc = eGameTextures::interface();
    const auto uiScale = resolution().uiScale();
    const int icoll = static_cast<int>(uiScale);
    const int mult = icoll + 1;
    const auto& coll = intrfc[icoll];
    setPadding(0);

    const auto s0 = new eWidget(window());
    s0->setWidth(mult*20);

    mDrachmasWidget = new eTopWidget(window());
    mDrachmasWidget->initialize(coll.fDrachmasTopMenu, "-");

    const auto s1 = new eWidget(window());
    s1->setWidth(mult*20);

    mCityLabel = new eLabel("-", window());
#ifdef __ANDROID__
    // Same reasoning as eTopWidget: the desktop small size is unreadable
    // on a phone screen.
    mCityLabel->setFontSize(resolution().touchFontSize(resolution().smallFontSize()));
#else
    mCityLabel->setSmallFontSize();
#endif
    mCityLabel->setNoPadding();
    mCityLabel->fitContent();

    const auto s2 = new eWidget(window());
    s2->setWidth(mult*20);

    mPopulationWidget = new eTopWidget(window());
    mPopulationWidget->initialize(coll.fPopulationTopMenu, "-");

    const auto s3 = new eWidget(window());
    s3->setWidth(mult*20);

    mDateLabel = new eButton(window());
    mDateLabel->setPressAction([this]() {
        if(!mBoard) return;
        const auto dw = new eDateWidget(window());
        dw->initialize([this](const eDate& d) {
            mBoard->setDate(d);
            mDateLabel->setText(d.shortString());
        }, false);
        dw->setDate(mBoard->date());
        window()->execDialog(dw);
        dw->align(eAlignment::center);
    });
    const eDate date(30, eMonth::january, -1500);
#ifdef __ANDROID__
    mDateLabel->setFontSize(resolution().touchFontSize(resolution().smallFontSize()));
#else
    mDateLabel->setSmallFontSize();
#endif
    mDateLabel->setText(date.shortString());
    mDateLabel->fitContent();
    mDateLabel->setEnabled(false);

    const auto s4 = new eWidget(window());
    s4->setWidth(mult*15);

    addWidget(s0);
    addWidget(mCityLabel);
    addWidget(s1);
    addWidget(mDrachmasWidget);
    addWidget(s2);
    addWidget(mPopulationWidget);
    addWidget(s3);
    addWidget(mDateLabel);
    addWidget(s4);

#ifdef __ANDROID__
    // Grown to match the touch-scaled text set above; paintEvent() below
    // tiles the background texture vertically too so this doesn't leave
    // a gap under the bar.
    setHeight(resolution().touchFontSize(12*mult));
#else
    setHeight(12*mult);
#endif

    mCityLabel->align(eAlignment::vcenter);
    mDrachmasWidget->align(eAlignment::vcenter);
    mPopulationWidget->align(eAlignment::vcenter);
    mDateLabel->align(eAlignment::vcenter);

    layoutHorizontally();
}

void eTopBarWidget::setBoard(eGameBoard* const board) {
    mBoard = board;
}

void eTopBarWidget::setGameWidget(eGameWidget* const gw) {
    mGW = gw;
}

void eTopBarWidget::paintEvent(ePainter& p) {
    // const bool update = (++mTime % 60) == 0;
    if(mBoard) {
        const auto cid = mGW->viewedCity();
        const auto pid = mBoard->personPlayer();
//        const auto pid = mBoard->cityIdToPlayerId(cid);
        const auto& wb = mBoard->world();
        const auto c = wb.cityWithId(cid);

        const auto label = c ? c->name() : "-";
        mCityLabel->setText(label);
        mCityLabel->fitContent();

        const auto popData = mBoard->populationData(cid);
        if(popData) {
            const int pop = popData->population();
            mPopulationWidget->setText(std::to_string(pop));
        } else {
            mPopulationWidget->setText("-");
        }

        const int d = mBoard->drachmas(pid);
        mDrachmasWidget->setText(std::to_string(d));

        mDateLabel->setText(mBoard->date().shortString());
        mDateLabel->setEnabled(mBoard->editorMode());

        int iRes;
        int mult;
        iResAndMult(iRes, mult);
        const auto& intrfc = eGameTextures::interface()[iRes];
        const auto& tex = intrfc.fGameTopBar;
        const int texWidth = tex->width();
        const int texHeight = tex->height();
        const auto& rend = p.renderer();
        // On Android the bar is taller than a single tile (see
        // touchFontSize() above), so repeat the horizontal sweep down
        // the full height instead of leaving bare space underneath.
        for(int y = 0; y < height(); y += texHeight) {
            bool flip = false;
            for(int x = width() - texWidth; x > -texWidth; x -= texWidth) {
                tex->render(rend, x, y, flip);
                flip = !flip;
            }
        }
    } else {
        mDateLabel->setEnabled(false);
    }
}
