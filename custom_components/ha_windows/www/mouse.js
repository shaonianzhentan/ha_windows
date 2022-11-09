customElements.define("windows-mouse-panel", class extends LitElement {

    static get styles() {
        return css`
        .header{
            margin:10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        ha-card{
            min-height: 300px;
        }
        `
    }

    static get properties() {
        return {
            hass: {},
            tips: { type: String }
        }
    }

    constructor() {
        super()
        this.tips = '鼠标控制面板'
        this.supportTouch = 'ontouchstart' in window
    }

    setConfig(config) {
    }


    render() {
        return html`
        <div class="header">
          ${this.tips}
          <ha-switch @click=${this.change.bind(this)}></ha-switch>
        </div>
        <ha-card 
            @mousedown=${this.mousedown.bind(this)}
            @mouseup=${this.mouseup.bind(this)}
            @touchstart=${this.touchstart.bind(this)}
            @touchend=${this.touchend.bind(this)}        
        ></ha-card>`
    }

    connectedCallback() {
        super.connectedCallback()
        setTimeout(() => {
            this.renderRoot.querySelector('ha-switch').checked = storage.get('switch')
        }, 500)
    }


    fireEvent(data) {
        this.hass?.callApi('POST', 'events/ha_windows', data)
    }

    isSelected() {
        return this.renderRoot.querySelector('ha-switch').checked
    }

    change() {
        storage.set('switch', this.renderRoot.querySelector('ha-switch').checked)
        this.tips = '鼠标控制面板'
    }

    getOffsetLeft(element) {
        var actualLeft = element.offsetLeft;
        var current = element.offsetParent;
        while (current) {
            actualLeft += current.offsetLeft;
            current = current.offsetParent;
        }
        return actualLeft;
    }

    getOffsetTop(element) {
        var actualTop = element.offsetTop;
        var current = element.offsetParent;
        while (current) {
            actualTop += current.offsetTop;
            current = current.offsetParent;
        }
        return actualTop;
    }

    touchstart() {
        if (this.isSelected() == false) return;
        const event = arguments[arguments.length - 1]
        const element = event.path[0]
        const { pageX, pageY } = event.changedTouches[0]
        this.down(element.offsetWidth, pageX - this.getOffsetLeft(element), pageY - this.getOffsetTop(element))
        event.preventDefault()
    }

    touchend() {
        if (this.isSelected() == false) return;
        const event = arguments[arguments.length - 1]
        const element = event.path[0]
        const { pageX, pageY } = event.changedTouches[0]
        this.up(pageX - this.getOffsetLeft(element), pageY - this.getOffsetTop(element))
    }

    mousedown() {
        if (this.supportTouch) return;
        if (this.isSelected() == false) return;
        const event = arguments[arguments.length - 1]
        const width = event.path[0].offsetWidth
        this.down(width, event.offsetX, event.offsetY)
        // console.log('鼠标按下', event.offsetX, event.offsetY)
    }

    mouseup() {
        if (this.supportTouch) return;
        if (this.isSelected() == false) return;
        const event = arguments[arguments.length - 1]
        this.up(event.offsetX, event.offsetY)
        // console.log('鼠标放开', event.offsetX, event.offsetY)
    }

    down(width, x, y) {
        this.mouse = { width, x, y }
    }

    up(offsetX, offsetY) {
        if (this.mouse != null) {
            const { width, x, y } = this.mouse
            const pos = {
                x: parseInt(offsetX - x),
                y: parseInt(offsetY - y)
            }
            // 点击
            if (pos.x == 0 && pos.y == 0) {
                if (x > width / 2) {
                    this.tips = '点击了右键'
                    this.fireEvent({ type: 'exe', data: 'mouse_right_click' })
                } else {
                    this.tips = '点击了左键'
                    this.fireEvent({ type: 'exe', data: 'mouse_left_click' })
                }
            } else {
                this.tips = `移动了鼠标：${pos.x}，${pos.y}`
                this.fireEvent({ type: 'exe', data: `mouse_move ${pos.x},${pos.y}` })
            }
            this.mouse = null
        }
    }
});

// 添加预览
window.customCards = window.customCards || [];
window.customCards.push({
    type: "windows-mouse-panel",
    name: "Windows鼠标控制面板",
    preview: true,
    description: "此功能需要配置【家庭助理】Windows应用使用"
});