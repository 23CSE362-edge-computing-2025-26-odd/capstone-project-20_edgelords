import numpy as np
import matplotlib.pyplot as plt

class FuzzyDistanceController:
    def __init__(self):
        self.transitions = {
            'very_close': {'center': 10, 'steepness': 0.3},
            'close': {'center': 40, 'steepness': 0.2},
            'far': {'center': 60, 'steepness': 0.15},
            'very_far': {'center': 100, 'steepness': 0.1}
        }
    
    def smooth_sigmoid(self, x, center, steepness, direction='decreasing'):
        if direction == 'decreasing':
            return 1 / (1 + np.exp(steepness * (x - center)))
        else:
            return 1 / (1 + np.exp(-steepness * (x - center)))
    
    def calculate_memberships(self, distance):
        vc = self.smooth_sigmoid(distance, 
                               self.transitions['very_close']['center'],
                               self.transitions['very_close']['steepness'],
                               'decreasing')
        
        c = self.smooth_sigmoid(distance,
                              self.transitions['close']['center'],
                              self.transitions['close']['steepness'],
                              'decreasing')
        
        f = self.smooth_sigmoid(distance,
                              self.transitions['far']['center'],
                              self.transitions['far']['steepness'],
                              'increasing')
        
        vf = self.smooth_sigmoid(distance,
                               self.transitions['very_far']['center'],
                               self.transitions['very_far']['steepness'],
                               'increasing')
        
        return {
            'very_close': vc,
            'close': c,
            'far': f,
            'very_far': vf
        }
    
    def calculate_score(self, distance):
        memberships = self.calculate_memberships(distance)
        
        stop_influence = memberships['very_close']
        
        slow_influence = (memberships['close'] * 0.8 + 
                         memberships['very_close'] * 0.2)
        
        go_influence = (memberships['far'] * 0.4 + 
                       memberships['very_far'] * 0.6)
        
        total_influence = stop_influence + slow_influence + go_influence
        if total_influence == 0:
            return 0.5, memberships
        
        base_score = (stop_influence * 1.0 + 
                     slow_influence * 0.5 + 
                     go_influence * 0.1) / total_influence
        
        final_score = 1 / (1 + np.exp(-8 * (base_score - 0.5)))
        
        return final_score, memberships
    
    def get_action(self, distance):
        score, memberships = self.calculate_score(distance)
        
        if score >= 0.6:
            return "STOP", score
        elif score >= 0.3:
            return "SLOW DOWN", score
        else:
            return "GO", score
    
    def plot_system(self):
        distances = np.linspace(0, 160, 400)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        vc_memberships = [self.calculate_memberships(d)['very_close'] for d in distances]
        c_memberships = [self.calculate_memberships(d)['close'] for d in distances]
        f_memberships = [self.calculate_memberships(d)['far'] for d in distances]
        vf_memberships = [self.calculate_memberships(d)['very_far'] for d in distances]
        
        ax1.plot(distances, vc_memberships, label='Very Close', linewidth=3, color='red')
        ax1.plot(distances, c_memberships, label='Close', linewidth=3, color='orange')
        ax1.plot(distances, f_memberships, label='Far', linewidth=3, color='lightblue')
        ax1.plot(distances, vf_memberships, label='Very Far', linewidth=3, color='blue')
        
        ax1.axvline(x=self.transitions['very_close']['center'], color='red', linestyle='--', alpha=0.5, label='VC center')
        ax1.axvline(x=self.transitions['close']['center'], color='orange', linestyle='--', alpha=0.5, label='C center')
        ax1.axvline(x=self.transitions['far']['center'], color='lightblue', linestyle='--', alpha=0.5, label='F center')
        ax1.axvline(x=self.transitions['very_far']['center'], color='blue', linestyle='--', alpha=0.5, label='VF center')
        
        ax1.set_title('Smooth Sigmoidal Membership Functions')
        ax1.set_xlabel('Distance (cm)')
        ax1.set_ylabel('Membership Degree')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, 160)
        ax1.set_ylim(-0.05, 1.05)
        
        scores = [self.calculate_score(d)[0] for d in distances]
        ax2.plot(distances, scores, 'purple', linewidth=4, label='Action Score')

        ax2.axhline(y=0.6, color='red', linestyle='--', linewidth=2, label='STOP')
        ax2.axhline(y=0.3, color='orange', linestyle='--', linewidth=2, label='SLOW')
        
        stop_end = next((d for d, s in zip(distances, scores) if s < 0.6), 160)
        slow_end = next((d for d, s in zip(distances, scores) if s < 0.3), 160)

        ax2.axvspan(0, stop_end, alpha=0.15, color='red', label='Stop Zone')
        ax2.axvspan(stop_end, slow_end, alpha=0.15, color='orange', label='Slow Zone')
        ax2.axvspan(slow_end, 160, alpha=0.15, color='green', label='Go Zone')
        
        test_points = [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 160]
        for dist in test_points:
            action, score = self.get_action(dist)
            color = 'red' if action == "STOP" else 'orange' if action == "SLOW DOWN" else 'green'
            ax2.plot(dist, score, 'o', markersize=8, color=color, markeredgecolor='black')
            ax2.annotate(f'{dist}cm', (dist, score), xytext=(5, 5), 
                        textcoords='offset points', fontsize=8)
        
        ax2.set_title('Action Score with New Thresholds (STOP ≥ 0.6, SLOW ≥ 0.3)')
        ax2.set_xlabel('Distance (cm)')
        ax2.set_ylabel('Action Score')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(-0.05, 1.05)
        ax2.set_xlim(0, 160)
        
        plt.tight_layout()
        plt.show()

def main():
    fuzzy_controller = FuzzyDistanceController()
    
    test_distances = [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 160]
    
    print("Fuzzy Distance Controller - New Thresholds")
    print("=" * 65)
    print("Very Close: Decreasing sigmoid centered at 10cm")
    print("Close: Decreasing sigmoid centered at 40cm")
    print("Far: Increasing sigmoid centered at 60cm")
    print("Very Far: Increasing sigmoid centered at 100cm")
    print("Thresholds: STOP ≥ 0.6, SLOW DOWN ≥ 0.3")
    print("=" * 65)
    
    for dist in test_distances:
        action, score = fuzzy_controller.get_action(dist)
        memberships = fuzzy_controller.calculate_memberships(dist)
        
        action_icon = "🛑" if action == "STOP" else "🚧" if action == "SLOW DOWN" else "🟢"
        print(f"{action_icon} {dist:3d}cm: {action:10} Score: {score:.3f}")
        print(f"     VC: {memberships['very_close']:.3f}, C: {memberships['close']:.3f}, "
              f"F: {memberships['far']:.3f}, VF: {memberships['very_far']:.3f}")
        print()
    
    fuzzy_controller.plot_system()

if __name__ == "__main__":
    main()