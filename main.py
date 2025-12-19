from gift_system import build, view, clear_screen


def main_menu():
    while True:
        clear_screen()

        print("\n=== SYSTÈME D’ATTRIBUTION DE CADEAUX ===")
        print("1 - Générer les assignations")
        print("2 - Voir mon attribution")
        print("0 - Quitter")

        choice = input("\n>>>> ").strip()

        if choice in [ "1", "2"]:
            clear_screen()

            if choice == "1":
                employees_file = input("Chemin du fichier employés : ").strip()
                build(employees_file)

            elif choice == "2":
                view()
                input("Appuyez sur n'importe quelle touche pour revenir au menu")

        elif choice == "0":
            print("Au revoir.")
            break

        else:
            print("Choix invalide.")


if __name__ == "__main__":
    main_menu()
