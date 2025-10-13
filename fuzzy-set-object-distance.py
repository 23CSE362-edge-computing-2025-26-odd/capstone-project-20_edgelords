import numpy as np
import matplotlib.pyplot as plt

class FuzzyDistanceController:
    def __init__(self):
        self.memberships = {
            'very_far': {'center': 100, 'width': 40},
            'far': {'center': 80, 'width': 40},
            'close': {'center': 40, 'width': 40},
            'very_close': {'center': 20, 'width': 40}
        }
        
    def s_curve_membership(self, x, center, width):
        steepness = 6.0 / width
        return 1 / (1 + np.exp(-steepness * (x - center)))
    
    def calculate_memberships(self, distance):
        memberships = {}
        for name, params in self.memberships.items():
            if name in ['very_far', 'far']:
                memberships[name] = 1 - self.s_curve_membership(
                    distance, params['center'], params['width'])
            else:
                memberships[name] = self.s_curve_membership(
                    distance, params['center'], params['width'])
        return memberships
    
    def defuzzify(self, distance):
        memberships = self.calculate_memberships(distance)
        
        stop_strength = max(memberships['very_close'], memberships['close'])
        go_strength = max(memberships['far'], memberships['very_far'])
        
        total = stop_strength + go_strength
        if total == 0:
            return 0.5
            
        crisp_output = stop_strength / total
        return crisp_output
    
    def get_action(self, distance):
        output = self.defuzzify(distance)
        
        if output >= 0.7:
            return "STOP", output
        elif output >= 0.4:
            return "SLOW DOWN", output
        else:
            return "GO", output
    
    def plot_memberships(self):
        distances = np.linspace(0, 120, 200)
        
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 1, 1)
        for name, params in self.memberships.items():
            if name in ['very_far', 'far']:
                memberships = [1 - self.s_curve_membership(d, params['center'], params['width']) 
                             for d in distances]
            else:
                memberships = [self.s_curve_membership(d, params['center'], params['width']) 
                             for d in distances]
            plt.plot(distances, memberships, label=name.replace('_', ' ').title(), linewidth=2)
        
        plt.title('Fuzzy Membership Functions')
        plt.xlabel('Distance (cm)')
        plt.ylabel('Membership Degree')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 1, 2)
        outputs = [self.defuzzify(d) for d in distances]
        plt.plot(distances, outputs, 'r-', linewidth=3, label='Stop Signal Strength')
        plt.axhline(y=0.7, color='orange', linestyle='--', label='Stop Threshold')
        plt.axhline(y=0.4, color='yellow', linestyle='--', label='Slow Down Threshold')
        
        plt.title('Defuzzified Output (Stop Signal)')
        plt.xlabel('Distance (cm)')
        plt.ylabel('Stop Signal Strength\n(0=Go, 1=Stop)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.ylim(-0.1, 1.1)
        
        plt.tight_layout()
        plt.show()

#TODO: replace with actual sensor readings
def main():
    fuzzy_controller = FuzzyDistanceController()
    
    test_distances = [10, 25, 35, 50, 70, 90, 110]
    
    print("Fuzzy Distance Controller Results:")
    
    for dist in test_distances:
        action, score = fuzzy_controller.get_action(dist)
        memberships = fuzzy_controller.calculate_memberships(dist)
        
        print(f"Distance: {dist:3d}cm | Action: {action:10} | "
              f"Stop Score: {score:.3f}")
        print(f"  Memberships - Very Close: {memberships['very_close']:.3f}, "
              f"Close: {memberships['close']:.3f}, "
              f"Far: {memberships['far']:.3f}, "
              f"Very Far: {memberships['very_far']:.3f}")
        print()
    
    fuzzy_controller.plot_memberships()

if __name__ == "__main__":
    main()