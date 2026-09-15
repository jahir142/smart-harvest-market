// -------------------- NAVBAR TOGGLE --------------------
const menuIcon = document.querySelector(".menu-icon");
const navbar = document.querySelector(".navbar");

if (menuIcon && navbar) {
    menuIcon.addEventListener("click", () => {
        navbar.classList.toggle("active");
    });
}

// Close navbar on scroll (safe — no undefined variables)
window.addEventListener("scroll", () => {
    if (navbar) navbar.classList.remove("active");
});

// -------------------- WHATSAPP CHAT --------------------
function toggleChat() {
    const chat = document.getElementById('chatBoard');
    if (chat) {
        chat.style.display = (chat.style.display === 'block') ? 'none' : 'block';
    }
}

// -------------------- PRODUCT BTN → localStorage --------------------
// Saves selected product when any .product-btn (Order link) is clicked
document.addEventListener("click", function (e) {
    const btn = e.target.closest(".product-btn");
    if (!btn) return;

    // Only store + navigate if it has data-name (Order buttons)
    if (btn.dataset.name) {
        const productData = {
            name: btn.dataset.name,
            price: btn.dataset.price,
            image: btn.dataset.image
        };
        localStorage.setItem("selectedProduct", JSON.stringify(productData));
        // Allow the link href (/order) to proceed naturally
    }
});

// -------------------- ORDER PAGE SCRIPT --------------------
// Only runs if order page elements exist
const productNameEl  = document.getElementById("productName");
const productImageEl = document.getElementById("productImage");
const priceEl        = document.getElementById("price");

if (productNameEl && productImageEl && priceEl) {
    const selectedProduct = JSON.parse(localStorage.getItem("selectedProduct"));

    if (selectedProduct) {
        productNameEl.innerText  = selectedProduct.name;
        priceEl.innerText        = selectedProduct.price;
        productImageEl.src       = selectedProduct.image;
    }

    let basePrice        = selectedProduct ? parseFloat(selectedProduct.price) : 0;
    let weightMultiplier = 1;
    let orderPlaced      = false;

    const qtyInput = document.getElementById("qty");

    function updatePrice() {
        const quantity = parseInt(qtyInput.value) || 1;
        priceEl.innerText = (basePrice * weightMultiplier * quantity).toFixed(2);
    }

    updatePrice();
    if (qtyInput) qtyInput.addEventListener("input", updatePrice);

    // Weight buttons
    document.querySelectorAll(".weight button").forEach(b => {
        b.onclick = () => {
            document.querySelectorAll(".weight button").forEach(x => x.classList.remove("active"));
            b.classList.add("active");
            weightMultiplier = parseInt(b.dataset.mult);
            updatePrice();
        };
    });

    // Place order button
    const buyNowBtn = document.getElementById("buyNow");
    if (buyNowBtn) {
        buyNowBtn.onclick = () => {
            if (orderPlaced) return;

            const custName  = document.getElementById("custName");
            const custPhone = document.getElementById("custPhone");
            const custEmail = document.getElementById("custEmail");
            const custNote  = document.getElementById("custNote");

            if (!custName.value || !custPhone.value || !qtyInput.value) {
                alert("Please enter your Name, Phone and Quantity.");
                return;
            }

            const orderData = {
                product:  selectedProduct ? selectedProduct.name : "",
                weight:   document.querySelector(".weight button.active")?.innerText || "0.5 Kg",
                quantity: qtyInput.value,
                payment:  "Cash on Delivery",
                price:    (basePrice * weightMultiplier * parseInt(qtyInput.value)).toFixed(2),
                name:     custName.value,
                email:    custEmail ? custEmail.value || "-" : "-",
                phone:    custPhone.value,
                note:     custNote ? custNote.value || "-" : "-"
            };

            // Show summary popup
            const alertImg    = document.getElementById("alertImg");
            const alertName   = document.getElementById("alertName");
            const alertWeight = document.getElementById("alertWeight");
            const alertQty    = document.getElementById("alertQty");
            const alertPay    = document.getElementById("alertPay");
            const alertPrice  = document.getElementById("alertPrice");
            const aName       = document.getElementById("aName");
            const aEmail      = document.getElementById("aEmail");
            const aPhone      = document.getElementById("aPhone");
            const aNote       = document.getElementById("aNote");
            const customAlert = document.getElementById("customAlert");

            if (alertImg)    alertImg.src             = selectedProduct ? selectedProduct.image : "";
            if (alertName)   alertName.innerText       = orderData.product;
            if (alertWeight) alertWeight.innerText     = orderData.weight;
            if (alertQty)    alertQty.innerText        = orderData.quantity;
            if (alertPay)    alertPay.innerText        = orderData.payment;
            if (alertPrice)  alertPrice.innerText      = orderData.price;
            if (aName)       aName.innerText           = orderData.name;
            if (aEmail)      aEmail.innerText          = orderData.email;
            if (aPhone)      aPhone.innerText          = orderData.phone;
            if (aNote)       aNote.innerText           = orderData.note;
            if (customAlert) customAlert.style.display = "flex";

            // Send to backend
            fetch("/place_order", {
                method:  "POST",
                headers: { "Content-Type": "application/json" },
                body:    JSON.stringify(orderData)
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) console.error("Order error:", data.error);
            })
            .catch(err => console.error("Network error:", err));

            orderPlaced = true;
        };
    }

    // Close alert popup
    const okAlertBtn    = document.getElementById("okAlert");
    const closeAlertBtn = document.getElementById("closeAlert");

    function closeAlertPopup() {
        const customAlert = document.getElementById("customAlert");
        if (customAlert) customAlert.style.display = "none";
    }

    if (okAlertBtn)    okAlertBtn.onclick    = closeAlertPopup;
    if (closeAlertBtn) closeAlertBtn.onclick = closeAlertPopup;
}
