import customtkinter as ctk
import re
import time
import threading
from datetime import datetime
 
class PaymentPage:
    def __init__(self, master=None, on_success=None):
        self.master = master
        self.on_success = on_success
        self.root = ctk.CTkToplevel(self.master) if self.master else ctk.CTk()
        self.root.title("JARVIS - Upgrade to Plus")
        # Full screen
        self.root.after(0, lambda: self.root.state("zoomed"))
        self.root.configure(fg_color="#0a0a0f") # Deep space background
        self.create_widgets()
 
    def create_widgets(self):
        # 1. Main Centered Container (The "Card")
        # This prevents the stretching by setting a fixed width
        self.card = ctk.CTkFrame(self.root, width=500, fg_color="#16161e", corner_radius=20, border_width=1, border_color="#2a2a35")
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False) # Keep width fixed
        self.card.configure(height=850) # Set a comfortable height
 
        # --- Header Section ---
        ctk.CTkLabel(self.card, text="✨ JARVIS PLUS", font=("Inter", 12, "bold"), text_color="#4a5fe8").pack(pady=(40, 5))
        ctk.CTkLabel(self.card, text="Upgrade Your Experience", font=("Inter", 28, "bold")).pack(pady=5)
        # Features List (Small details make it look premium)
        features_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        features_frame.pack(pady=10)
        for feat in ["Priority AI Access", "Advanced Resume Analytics", "Unlimited Exports"]:
            row = ctk.CTkFrame(features_frame, fg_color="transparent")
            row.pack(anchor="w", pady=2)
            ctk.CTkLabel(row, text="✓", font=("Inter", 12, "bold"), text_color="#4a5fe8").pack(side="left")
            ctk.CTkLabel(row, text=feat, font=("Inter", 12), text_color="#888898").pack(side="left", padx=(5,0))
 
        # --- Plan Selection ---
        self.selected_plan = ctk.StringVar(value="monthly")
        selection_container = ctk.CTkFrame(self.card, fg_color="transparent")
        selection_container.pack(fill="x", padx=50, pady=20)

        # two columns side-by-side for clearer comparison
        left = ctk.CTkFrame(selection_container, fg_color="transparent")
        right = ctk.CTkFrame(selection_container, fg_color="transparent")
        left.pack(side="left", expand=True, fill="x", padx=5)
        right.pack(side="left", expand=True, fill="x", padx=5)

        # Monthly Option
        self.monthly_box = ctk.CTkFrame(left, fg_color="#1d1d26", border_width=2, border_color="#4a5fe8", height=120)
        self.monthly_box.pack(fill="x")
        self.monthly_box.pack_propagate(False)
        radio1 = ctk.CTkRadioButton(self.monthly_box, text="Monthly Billing", font=("Inter", 14, "bold"), 
                           variable=self.selected_plan, value="monthly")
        radio1.pack(anchor="w", padx=20, pady=(15,0))
        ctk.CTkLabel(self.monthly_box, text="$20/mo", font=("Inter", 16, "bold")).pack(anchor="w", padx=20, pady=(5,15))
        # clicking anywhere in the box selects it
        self.monthly_box.bind("<Button-1>", lambda e: self.selected_plan.set("monthly"))
        radio1.bind("<Button-1>", lambda e: self.selected_plan.set("monthly"))

        # Yearly Option
        self.yearly_box = ctk.CTkFrame(right, fg_color="#1d1d26", border_width=1, border_color="#2a2a35", height=120)
        self.yearly_box.pack(fill="x")
        self.yearly_box.pack_propagate(False)
        radio2 = ctk.CTkRadioButton(self.yearly_box, text="Yearly Billing", font=("Inter", 14), 
                           variable=self.selected_plan, value="yearly")
        radio2.pack(anchor="w", padx=20, pady=(15,0))
        ctk.CTkLabel(self.yearly_box, text="$200/yr", font=("Inter", 16, "bold"), text_color="#2cc985").pack(anchor="w", padx=20, pady=(5,0))
        ctk.CTkLabel(self.yearly_box, text="Save 17%", font=("Inter", 12, "italic"), text_color="#2cc985").pack(anchor="w", padx=20, pady=(0,15))
        self.yearly_box.bind("<Button-1>", lambda e: self.selected_plan.set("yearly"))
        radio2.bind("<Button-1>", lambda e: self.selected_plan.set("yearly"))
 
        # --- Payment method selector ---
        self.payment_method = ctk.StringVar(value="card")
        method_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        method_frame.pack(fill="x", padx=50, pady=(10,0))
        ctk.CTkRadioButton(method_frame, text="Card", variable=self.payment_method, value="card").pack(side="left", padx=20)
        ctk.CTkRadioButton(method_frame, text="UPI", variable=self.payment_method, value="upi").pack(side="left", padx=20)
        self.payment_method.trace_add("write", self.update_payment_ui)

        # --- Form Fields (Fixed Width) ---
        form_container = ctk.CTkFrame(self.card, fg_color="transparent")
        form_container.pack(fill="x", padx=50, pady=20)

        # card-specific container
        self.card_fields = ctk.CTkFrame(form_container, fg_color="transparent")
        self.card_fields.pack(fill="x")
        self.add_field(self.card_fields, "Cardholder Name", "John Doe", "name_entry")
        self.add_field(self.card_fields, "Card Number", "0000 0000 0000 0000", "card_entry")
        # attach formatting callback to card entry
        self.card_entry.bind("<KeyRelease>", self.format_card_number)

        # Row for Expiry and CVC
        # wrap both in a bordered frame so they appear as a single unit
        expiry_cvc_frame = ctk.CTkFrame(self.card_fields, fg_color="#1d1d26", corner_radius=10, border_width=1, border_color="#2a2a35")
        expiry_cvc_frame.pack(fill="x", pady=5, padx=0)
        row = expiry_cvc_frame
        # Left side of row
        e_frame = ctk.CTkFrame(row, fg_color="transparent")
        e_frame.pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkLabel(e_frame, text="Expiry Date", font=("Inter", 12)).pack(anchor="w")
        self.expiry_entry = ctk.CTkEntry(e_frame, placeholder_text="MM/YY", height=45, fg_color="#0f0f15", border_color="#2a2a35")
        self.expiry_entry.pack(fill="x")

        # Right side of row
        c_frame = ctk.CTkFrame(row, fg_color="transparent")
        c_frame.pack(side="left", fill="x", expand=True, padx=(5,0))
        ctk.CTkLabel(c_frame, text="CVC", font=("Inter", 12)).pack(anchor="w")
        self.cvc_entry = ctk.CTkEntry(c_frame, placeholder_text="123", height=45, fg_color="#0f0f15", border_color="#2a2a35")
        self.cvc_entry.pack(fill="x")

        # upi-specific container (hidden initially)
        self.upi_fields = ctk.CTkFrame(form_container, fg_color="transparent")
        self.upi_fields.pack(fill="x")
        self.add_field(self.upi_fields, "UPI ID", "someone@bank", "upi_entry")
        self.upi_fields.pack_forget()

        # ensure correct fields visible based on default payment method
        self.update_payment_ui()

        # --- Bottom Buttons ---
        self.subscribe_btn = ctk.CTkButton(self.card, text="Confirm Subscription", height=50, 
                                          fg_color="#4a5fe8", hover_color="#3b4dbf", 
                                          font=("Inter", 16, "bold"), command=self.handle_subscribe)
        # make button stretch to edges visually
        self.subscribe_btn.pack(fill="x", padx=50, pady=(30, 10))
 
        self.cancel_btn = ctk.CTkButton(self.card, text="Back to Free Tier", fg_color="transparent", 
                                       text_color="#666676", hover=False, command=self.root.destroy)
        self.cancel_btn.pack(pady=10)
 
        self.message_label = ctk.CTkLabel(self.card, text="", font=("Inter", 12))
        self.message_label.pack(pady=5)
 
        # Plan toggle animation logic
        self.selected_plan.trace_add("write", self.update_plan_ui)
        # enforce initial styling based on default selection
        self.update_plan_ui()
 
    def add_field(self, parent, label, placeholder, attr_name):
        ctk.CTkLabel(parent, text=label, font=("Inter", 12)).pack(anchor="w", pady=(10, 5))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=45, fg_color="#0f0f15", border_color="#2a2a35")
        entry.pack(fill="x")
        setattr(self, attr_name, entry)
 
    def update_plan_ui(self, *args):
        # visually distinguish the selected box by border and background
        if self.selected_plan.get() == "monthly":
            self.monthly_box.configure(border_color="#4a5fe8", border_width=2, fg_color="#26262e")
            self.yearly_box.configure(border_color="#2a2a35", border_width=1, fg_color="#1d1d26")
        else:
            self.yearly_box.configure(border_color="#4a5fe8", border_width=2, fg_color="#26262e")
            self.monthly_box.configure(border_color="#2a2a35", border_width=1, fg_color="#1d1d26")
        # make the radio button reflect selection (necessary if clicking label)
        # nothing else since radios already bound to variable
 
    def update_payment_ui(self, *args):
        method = self.payment_method.get()
        if method == "card":
            self.card_fields.pack(fill="x")
            self.upi_fields.pack_forget()
        else:
            self.card_fields.pack_forget()
            self.upi_fields.pack(fill="x")

    def handle_subscribe(self):
        method = self.payment_method.get()
        if method == "card":
            name = self.name_entry.get().strip()
            card_num = self.card_entry.get().replace(" ", "").strip()
            expiry = self.expiry_entry.get().replace(" ", "").strip()
            cvc = self.cvc_entry.get().strip()

            if not all([name, card_num, expiry, cvc]):
                self.message_label.configure(text="Please fill all payment fields.", text_color="red")
                return
            # remove any spaces that may have been inserted by formatter
            card_num = re.sub(r"\s+", "", card_num)

            # Validate Card Number
            if not re.match(r"^\d{16}$", card_num):
                self.message_label.configure(text="Invalid card number (must be 16 digits).", text_color="red")
                return

            # Validate Expiry Date
            if not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", expiry):
                self.message_label.configure(text="Invalid expiry format (MM/YY).", text_color="red")
                return
            
            try:
                exp_month, exp_year = map(int, expiry.split('/'))
                current_date = datetime.now()
                # Assuming year is 20xx
                exp_year += 2000
                if exp_year < current_date.year or (exp_year == current_date.year and exp_month < current_date.month):
                    self.message_label.configure(text="Card has expired.", text_color="red")
                    return
            except Exception:
                self.message_label.configure(text="Invalid expiry date.", text_color="red")
                return

            # Validate CVC
            if not re.match(r"^\d{3,4}$", cvc):
                self.message_label.configure(text="Invalid CVC (3-4 digits).", text_color="red")
                return
        else:
            # UPI flow
            upi_id = self.upi_entry.get().strip()
            if not upi_id:
                self.message_label.configure(text="Please enter your UPI ID.", text_color="red")
                return
            # simple pattern check (word@word)
            if not re.match(r"^[\w\.\-]+@[\w]+$", upi_id):
                self.message_label.configure(text="Invalid UPI ID format.", text_color="red")
                return

        self.subscribe_btn.configure(text="Securing Connection...", state="disabled")
        self.cancel_btn.configure(state="disabled")
        self.message_label.configure(text="")
        
        def process():
            time.sleep(2)
            self.root.after(0, self.show_success)
        threading.Thread(target=process, daemon=True).start()
 
    def show_success(self):
        self.message_label.configure(text="✓ Subscription Successful!", text_color="#2cc985")
        self.subscribe_btn.configure(text="Welcome to Plus", fg_color="#2cc985")
        if self.on_success: self.on_success()
        self.root.after(2000, self.root.destroy)
 
    def run(self):
        if self.master:
            self.root.transient(self.master)
            self.root.grab_set()
        self.root.mainloop()

    def format_card_number(self, event=None):
        """Automatically insert spaces every 4 digits in the card entry."""
        text = self.card_entry.get()
        digits = re.sub(r"\D", "", text)  # strip non‑digits
        chunks = [digits[i:i+4] for i in range(0, len(digits), 4)]
        new_text = " ".join(chunks)
        if new_text != text:
            self.card_entry.delete(0, "end")
            self.card_entry.insert(0, new_text)
            # keep cursor at end
            self.card_entry.icursor("end")

if __name__ == "__main__":
    app = PaymentPage()
    app.run()
