class ReportService:
    @staticmethod
    def generate_report(trucks):
        report_data = []
        fleet_avg_sum = 0
        valid_trucks = 0

        for truck in trucks:
            samples = truck.history
            count = len(samples)
            
            if count == 0:
                report_data.append({
                    "id": truck.truck_id,
                    "count": 0, "min": 0, "max": 0, "avg": 0
                })
                continue
                
            speeds = [s["speed"] for s in samples]
            min_speed = round(min(speeds), 2)
            max_speed = round(max(speeds), 2)
            avg_speed = round(sum(speeds) / count, 2)
            
            report_data.append({
                "id": truck.truck_id,
                "count": count,
                "min": min_speed,
                "max": max_speed,
                "avg": avg_speed
            })
            
            fleet_avg_sum += avg_speed
            valid_trucks += 1

        #Lógica Heurística
        heuristic_text = ReportService._generate_heuristic(report_data, fleet_avg_sum, valid_trucks)

        return {
            "metrics": report_data,
            "explanation": heuristic_text
        }

    @staticmethod
    def _generate_heuristic(report_data, fleet_avg_sum, valid_trucks):
        if valid_trucks == 0:
            return "La simulación aún no ha recolectado datos suficientes."

        fleet_avg = round(fleet_avg_sum / valid_trucks, 2)
        
        active = [r for r in report_data if r["count"] > 0]
        active.sort(key=lambda x: x["avg"])
        
        slowest = active[0]
        fastest = active[-1]
        
        lines = []
        lines.append(f"El promedio general de la flota es de {fleet_avg} km/h.")
        
        lines.append(f"El vehículo más rápido en promedio fue el {fastest['id']} con {fastest['avg']} km/h, "
                     f"mientras que el más lento fue el {slowest['id']} con {slowest['avg']} km/h.")
                     
        low_samples = [r['id'] for r in active if r['count'] < 10]
        if low_samples:
            lines.append(f"Advertencia: Los camiones {', '.join(low_samples)} tienen menos de 10 muestras de velocidad, "
                         "por lo que su promedio podría no ser estadísticamente representativo.")
                         
        return " ".join(lines)