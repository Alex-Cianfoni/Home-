"""Tkinter submarine selection dialog; no external UI dependencies."""
from __future__ import annotations

from submarine_catalog import SUBMARINES, DEFAULT_SUBMARINE, groups


def choose_submarine(parent, initial: str = DEFAULT_SUBMARINE):
    import tkinter as tk
    from tkinter import ttk

    DARK, PANEL, FG, MUTED, GREEN = "#071827", "#102a3a", "#dfeef5", "#a1bfc9", "#75eeb4"
    window = tk.Toplevel(parent)
    window.title("Fleet Command  |  Select Your Submarine")
    window.geometry("900x620")
    window.minsize(700, 470)
    window.configure(bg=DARK)
    window.transient(parent)
    window.grab_set()
    result = [None]
    filtered = []
    selected = [initial if initial in SUBMARINES else DEFAULT_SUBMARINE]

    header = tk.Frame(window,bg=DARK)
    header.pack(fill="x",padx=22,pady=(18,12))
    tk.Label(header,text="CHOOSE YOUR COMMAND",bg=DARK,fg=GREEN,font=("Consolas",21,"bold")).pack(anchor="w")
    tk.Label(header,text=f"{len(SUBMARINES)} playable submarine classes and historic hulls • game-balanced specifications",
             bg=DARK,fg=MUTED,font=("Arial",10)).pack(anchor="w")

    filters=tk.Frame(window,bg=DARK)
    filters.pack(fill="x",padx=22,pady=(0,12))
    search_var=tk.StringVar()
    category_var=tk.StringVar(value="All categories")
    ttk.Entry(filters,textvariable=search_var).pack(side="left",fill="x",expand=True,padx=(0,10),ipady=4)
    category=ttk.Combobox(filters,textvariable=category_var,values=["All categories"]+sorted(groups()),state="readonly",width=27)
    category.pack(side="right")

    body=tk.PanedWindow(window,orient="horizontal",bg=DARK,sashwidth=6,relief="flat",borderwidth=0)
    body.pack(fill="both",expand=True,padx=20,pady=(0,14))
    left=tk.Frame(body,bg=PANEL)
    right=tk.Frame(body,bg=PANEL)
    body.add(left, minsize=260)
    body.add(right, minsize=260)
    scroll=tk.Scrollbar(left)
    scroll.pack(side="right",fill="y")
    listing=tk.Listbox(left,bg=PANEL,fg=FG,selectbackground="#17694e",selectforeground="white",
                       activestyle="none",font=("Consolas",10),borderwidth=0,highlightthickness=0,
                       exportselection=False,yscrollcommand=scroll.set)
    listing.pack(fill="both",expand=True,padx=6,pady=6)
    scroll.configure(command=listing.yview)

    details=tk.Text(right,bg=PANEL,fg=FG,wrap="word",font=("Consolas",11),borderwidth=0,highlightthickness=0,padx=18,pady=20)
    details.pack(fill="both",expand=True)
    details.configure(state="disabled")

    def show_details():
        sub=SUBMARINES[selected[0]]
        lines=[sub.name,"",f"NAVY           {sub.country}",f"CATEGORY       {sub.era}",
               f"ORIGINAL YEAR  {sub.year}","", "GAME SIMULATION STATISTICS", "--------------------------",
               f"Max speed      {sub.speed:g} knots",f"Dive limit     {sub.depth} feet",
               f"Starting power {sub.battery}%",f"Sonar rating   {sub.sonar}/10",
               f"Noise index    {sub.signature}/10 (low = quiet)",
               f"Torpedoes      {sub.torpedoes}","",sub.description,"",
               "All ships use fictional 2026-modernized systems for balanced gameplay.",
               "The listed limits are NOT historical technical specifications."]
        details.configure(state="normal")
        details.delete("1.0","end")
        details.insert("end","\n".join(lines))
        details.configure(state="disabled")

    def filter_ships(*_):
        txt=search_var.get().strip().casefold()
        cat=category_var.get()
        filtered.clear()
        listing.delete(0,"end")
        for sub in SUBMARINES.values():
            if cat != "All categories" and sub.era != cat:
                continue
            if txt not in (sub.name + " " + sub.country + " " + sub.era + " " + sub.description).casefold():
                continue
            filtered.append(sub.id)
            listing.insert("end",sub.name)
        if filtered:
            idx=filtered.index(selected[0]) if selected[0] in filtered else 0
            selected[0]=filtered[idx]
            listing.selection_set(idx)
            listing.see(idx)
            show_details()
        else:
            details.configure(state="normal")
            details.delete("1.0","end")
            details.insert("end","No matching submarine. Try another search term or category.")
            details.configure(state="disabled")

    def choose_index(_=None):
        indices=listing.curselection()
        if indices:
            selected[0]=filtered[indices[0]]
            show_details()

    def submit(_=None):
        if filtered and selected[0] in SUBMARINES:
            result[0]=selected[0]
            window.destroy()

    def cancel():
        window.destroy()

    listing.bind("<<ListboxSelect>>",choose_index)
    listing.bind("<Double-Button-1>",submit)
    listing.bind("<Return>",submit)
    search_var.trace_add("write",filter_ships)
    category_var.trace_add("write",filter_ships)
    filter_ships()

    footer=tk.Frame(window,bg=DARK)
    footer.pack(fill="x",padx=22,pady=(0,18))
    tk.Button(footer,text="CANCEL",command=cancel,fg=FG,bg="#264055",relief="flat",padx=18,pady=10).pack(side="right",padx=(8,0))
    tk.Button(footer,text="COMMAND THIS SUBMARINE",command=submit,fg="white",bg="#16674e",relief="flat",padx=20,pady=10,
              font=("Consolas",10,"bold")).pack(side="right")
    tk.Label(footer,text="Enter to select  •  Double-click to start",fg=MUTED,bg=DARK).pack(side="left")
    window.protocol("WM_DELETE_WINDOW",cancel)
    window.bind("<Escape>",lambda _:cancel())
    window.lift()
    window.focus_force()
    parent.wait_window(window)
    return result[0]
