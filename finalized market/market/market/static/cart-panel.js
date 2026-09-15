/* ============================================================
   SHARED CART PANEL JS — used by all category pages
   ============================================================ */

// ── TOGGLE ──
function openCartPanel() {
    document.getElementById('cartPanel').classList.add('open');
    document.getElementById('cartOverlay').classList.add('active');
    document.body.classList.add('cart-open');
}

function closeCartPanel() {
    document.getElementById('cartPanel').classList.remove('open');
    document.getElementById('cartOverlay').classList.remove('active');
    document.body.classList.remove('cart-open');
}

function toggleCartPanel() {
    const panel = document.getElementById('cartPanel');
    if (panel && panel.classList.contains('open')) {
        closeCartPanel();
    } else {
        openCartPanel();
    }
}

// ── RENDER CART ──
function renderCartPanel() {
    const cart      = JSON.parse(localStorage.getItem('cart') || '[]');
    const container = document.getElementById('cart-items-panel');
    const badge     = document.getElementById('cartBadge');

    if (!container) return;
    container.innerHTML = '';

    if (cart.length === 0) {
        container.innerHTML = '<p class="cart-empty-msg">Your cart is empty</p>';
        if (badge) badge.style.display = 'none';
    } else {
        if (badge) {
            badge.style.display = 'flex';
            badge.innerText = cart.reduce((s, i) => s + i.qty, 0);
        }
    }

    let total = 0;
    cart.forEach((item, index) => {
        total += item.price * item.qty;
        const row = document.createElement('div');
        row.className = 'cart-item-row';
        row.innerHTML = `
            <img src="${item.image}" alt="">
            <div class="item-info">
                <strong>${item.name}</strong>
                <span>x${item.qty} &nbsp;&#8377;${(item.price * item.qty).toFixed(2)}</span>
            </div>
            <button class="remove-item-btn" data-index="${index}">&times;</button>
        `;
        container.appendChild(row);
    });

    const totalEl = document.getElementById('cartPanelTotal');
    if (totalEl) totalEl.innerText = `Total: ₹${total.toFixed(2)}`;

    document.querySelectorAll('.remove-item-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const arr = JSON.parse(localStorage.getItem('cart') || '[]');
            arr.splice(parseInt(btn.dataset.index), 1);
            localStorage.setItem('cart', JSON.stringify(arr));
            renderCartPanel();
        });
    });
}

// ── SUCCESS TOAST — top-center, always visible ──
function showCartToast(msg) {
    let toast = document.getElementById('cartToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'cartToast';
        Object.assign(toast.style, {
            position:     'fixed',
            top:          '24px',
            left:         '50%',
            transform:    'translateX(-50%) translateY(-10px)',
            background:   '#00c9a5',
            color:        '#fff',
            padding:      '13px 30px',
            borderRadius: '30px',
            fontSize:     '15px',
            fontWeight:   '700',
            fontFamily:   'Arial, sans-serif',
            zIndex:       '99999',
            boxShadow:    '0 6px 24px rgba(0,0,0,0.2)',
            pointerEvents:'none',
            opacity:      '0',
            transition:   'opacity 0.3s ease, transform 0.3s ease',
            whiteSpace:   'nowrap'
        });
        document.body.appendChild(toast);
    }
    toast.innerHTML = '&#10003; ' + msg;
    toast.style.opacity   = '1';
    toast.style.transform = 'translateX(-50%) translateY(0)';
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
        toast.style.opacity   = '0';
        toast.style.transform = 'translateX(-50%) translateY(-10px)';
    }, 2500);
}

// ── ADD TO CART ──
function addToCartPanel(name, price, image, qty) {
    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const idx = cart.findIndex(i => i.name === name);
    if (idx >= 0) {
        cart[idx].qty += qty;
    } else {
        cart.push({ name, price: parseFloat(price), image, qty });
    }
    localStorage.setItem('cart', JSON.stringify(cart));
    renderCartPanel();

    // Flash toggle button red briefly
    const toggleBtn = document.getElementById('cartToggleBtn');
    if (toggleBtn) {
        toggleBtn.style.background = '#ff4b5c';
        setTimeout(() => { toggleBtn.style.background = ''; }, 500);
    }

    // Show "Successfully Added" toast
    showCartToast(name + ' successfully added!');
}

// ── CLEAR CART ──
function clearCart() {
    if (confirm('Clear all items from cart?')) {
        localStorage.setItem('cart', '[]');
        renderCartPanel();
    }
}

// ── DOM READY ──
document.addEventListener('DOMContentLoaded', () => {

    // Add-to-cart buttons (.add-cart-btn or .add-to-cart)
    document.querySelectorAll('.add-cart-btn, .add-to-cart').forEach(btn => {
        btn.addEventListener('click', () => {
            const card     = btn.closest('.cake-card');
            const qtyInput = card ? card.querySelector('.qty-input') : null;
            const qty      = qtyInput ? (parseInt(qtyInput.value) || 1) : 1;

            addToCartPanel(
                btn.dataset.name,
                btn.dataset.price,
                btn.dataset.image,
                qty
            );

            // Button visual feedback
            const orig = btn.textContent.trim();
            btn.textContent      = 'Added!';
            btn.style.background = '#009f88';
            setTimeout(() => {
                btn.textContent      = orig;
                btn.style.background = '';
            }, 1200);
        });
    });

    // Order buttons → save to localStorage → navigate
    document.querySelectorAll('.order-btn, .product-btn, .order-now-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.setItem('selectedProduct', JSON.stringify({
                name:  btn.dataset.name,
                price: btn.dataset.price,
                image: btn.dataset.image,
                unit:  btn.dataset.unit || 'kg'
            }));
            window.location.href = '/order';
        });
    });

    // Close panel when overlay clicked
    const overlay = document.getElementById('cartOverlay');
    if (overlay) overlay.addEventListener('click', closeCartPanel);

    // Initial render
    renderCartPanel();
});

// ================================================================
//  DAILY MARKET PRICE LOADER
//  Admin-ல set பண்ண prices → category pages-ல auto-update
// ================================================================
(async function loadDailyPrices() {
    try {
        const res    = await fetch('/api/prices');
        const prices = await res.json();
        if (!prices || Object.keys(prices).length === 0) return;

        const norm = s => (s || '').toLowerCase().trim()
                                   .replace(/\s+/g, ' ')
                                   .replace(/[^a-z0-9 ]/g, '');

        const priceMap = {};
        Object.entries(prices).forEach(([name, val]) => {
            if (val && val !== '__DELETE__') {
                priceMap[norm(name)] = val;
            }
        });

        // Strategy 1: data-item attribute
        document.querySelectorAll('[data-item]').forEach(el => {
            const val = priceMap[norm(el.dataset.item)];
            if (val) {
                el.innerText = '₹' + parseFloat(val).toFixed(2);
                _updateCardBtns(el.closest('.cake-card'), val);
            }
        });

        // Strategy 2: match by h3 text inside .cake-card
        document.querySelectorAll('.cake-card').forEach(card => {
            const h3 = card.querySelector('h3');
            if (!h3) return;
            const val = priceMap[norm(h3.innerText)];
            if (!val) return;
            const priceEl = card.querySelector('.price, [class*="price"]');
            if (priceEl) priceEl.innerText = '₹' + parseFloat(val).toFixed(2);
            _updateCardBtns(card, val);
        });

    } catch (e) { /* silent — page shows default prices */ }

    function _updateCardBtns(card, newPrice) {
        if (!card) return;
        card.querySelectorAll('.add-cart-btn,.add-to-cart,.order-btn,.order-now-btn,.product-btn')
            .forEach(b => { b.dataset.price = newPrice; });
    }
})();
