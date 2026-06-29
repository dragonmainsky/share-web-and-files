import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    
    def __init__(self):
        super().__init__()
        self.geometry("700x500")
        self.title("Hamburger Menu")

        self.menu_open = False
        self.menu_width = 200
        
        # -200 (width) + 10 (padding) + 40 (button width) + 10 (extra padding) = -140
        self.closed_x = -140  
        self.current_x = self.closed_x  # Start closed

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=self.menu_width, height=500, corner_radius=0)
        self.sidebar.place(x=self.current_x, y=0)

        # Hamburger button
        self.hamburger_btn = ctk.CTkButton(
            self.sidebar, text="☰", width=40, height=40,
            command=self.toggle_menu, font=("Arial", 20)
        )
        self.hamburger_btn.place(x=150, y=10) 

        # Menu Label
        self.menu_label = ctk.CTkLabel(self.sidebar, text="Menu", font=("Arial", 20, "bold"))
        # Start hidden because menu starts closed
        
        # Generate the menu buttons
        items = ["Setting"]
        self.menu_buttons = []
        
        for i, item in enumerate(items):
            btn = ctk.CTkButton(self.sidebar, text=item, width=160)
            btn.target_y = 120 + i * 50 
            self.menu_buttons.append(btn)

        # Main Content
        self.main_content = ctk.CTkLabel(self, text="Main Content Area", font=("Arial", 24))
        self.main_content.place(relx=0.5, rely=0.5, anchor="center")


    def toggle_menu(self):
        self.menu_open = not self.menu_open
        
        if self.menu_open:
            # --- OPENING: Show everything instantly ---
            self.menu_label.place(x=20, y=70)
            for btn in self.menu_buttons:
                btn.place(x=20, y=btn.target_y)
        else:
            # --- CLOSING: Hide everything INSTANTLY without waiting for animation ---
            self.menu_label.place_forget()
            for btn in self.menu_buttons:
                btn.place_forget()

        # Run the sidebar movement animation in the background
        self.animate()


    def animate(self):
        target = 0 if self.menu_open else self.closed_x
        diff = target - self.current_x
        
        if abs(diff) > 1:
            self.current_x += diff * 0.3
            self.sidebar.place(x=int(self.current_x), y=0)
            self.after(10, self.animate)
        else:
            self.current_x = target
            self.sidebar.place(x=target, y=0)


if __name__ == "__main__":
    app = App()
    app.mainloop()