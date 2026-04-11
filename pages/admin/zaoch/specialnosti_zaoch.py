from pages.admin.function_admin import BaseTableWidget

class ListSpecialnostiZao(BaseTableWidget):
    def __init__(self):
        super().__init__(
            table_name="public.specialities_evening",
            headers=[
                "ID", "Код спеціальності", "Код галузі знань", "Код і ім'я спеціальності", "Ліцензійний обсяг", "Держ. місця"
            ],
            sql_queries={
                "SELECT": """
                    SELECT id, kod_specialnosti, kod_galuzi, name_specialnosti, licensed_volume, state_places
                    FROM public.specialities_evening
                    ORDER BY id
                """,
                
                "DELETE": "DELETE FROM public.specialities_evening WHERE id = %s"
            },
            columns_name = [
                "id", "kod_specialnosti", "kod_galuzi", "name_specialnosti", "licensed_volume", "state_places"
            ], 
            label_text="Список спеціальностей (заочна форма)",
            default_values={
                "kod_specialnosti":"",
                "kod_galuzi":"",
                "name_specialnosti":"",
                "licensed_volume": 0,
                "state_places": 0
            }
        )

           