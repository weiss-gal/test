import random
import cProfile
from datetime import datetime

STUDENTS_NUM = 70
GROUP_NUM = 7
GROUP_SIZE = 10
PREFERENCE_NUM = 5

def rand_bool(probability=0.5):
    return random.random() < probability


class PreferenceStrategy:
    def get_preferences(self, preferences_num:int) -> list[int]:
        raise NotImplementedError("Subclasses must implement this method")

class IdenticalPreferenceStrategy(PreferenceStrategy):
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def get_preferences(self, student, preferences_num):
        return list(range(self.min, self.max))[:preferences_num]

class GaussianPreferenceStrategy(PreferenceStrategy):
    def __init__(self, min, max, std_dev=None):
        self.min = min
        self.max = max
        self.std_dev = std_dev if std_dev is not None else (max - min) / 3
    
    def get_preferences(self, student, preferences_num):
        preferences = []
        while len(preferences) < preferences_num:
            preference = int(random.gauss((self.min + self.max) / 2, self.std_dev))
            preference = max(self.min, min(self.max, preference))
            if preference not in preferences:
                preferences.append(preference)  

        return preferences

PREFERENCE_STRATEGY = GaussianPreferenceStrategy(0, GROUP_NUM-1, 2)
#PREFERENCE_STRATEGY = IdenticalPreferenceStrategy(0, GROUP_NUM)

class Student:
    def __init__(self, id, constraint_prob=0.5, preferences_num:int=PREFERENCE_NUM):
        self.id = id
        self.constraints = [rand_bool(constraint_prob) for i in range(0, GROUP_NUM)]
        self.preferences = PREFERENCE_STRATEGY.get_preferences(self, preferences_num)
        
    def __str__(self):
        return "Constraints: " + str(self.constraints) + "\nPreferences: " + str(self.preferences) + "\n"
    
    def check_assignment(self, group_id):
        return self.constraints[group_id]

students = [Student(i, 0.99) for i in range(0, STUDENTS_NUM)]
for i in range(STUDENTS_NUM):
    print(f"[{i}] {students[i]}")

class Assigment:
    def __init__(self):
        self.loss = 0
        self.assignments = [None for i in range(0, STUDENTS_NUM)]
        self.unassigned_students_cache = list(range(0, STUDENTS_NUM))
        self.empty_slots_per_group = [GROUP_SIZE for i in range(0, GROUP_NUM)]
        
    def __str__(self):
        return str(self.assignments) + "\nLoss: " + str(self.loss)
    
    def get_results(self):
        return self.assignments

    def check_assignment(self, student, group_id):
        return student.check_assignment(group_id) and self.empty_slots_per_group[group_id] > 0

    def get_student_loss(self, student, group_id):
        loss = 100
        for i in range(len(student.preferences)):
            if student.preferences[i] == group_id:
                loss = i * 10
                break
        return loss
    
    def get_unassigned_students(self):
        return self.unassigned_students_cache

    def assign(self, student, group_id):
        if len(self.unassigned_students_cache) == 0:
            raise Exception("No more groups available")
        
        self.assignments[student.id] = group_id
        self.empty_slots_per_group[group_id] -= 1
        self.unassigned_students_cache.remove(student.id)
        
        self.loss += self.get_student_loss(student, group_id)

    def recalculate_loss(self):
        """Recalculate the loss of the assignment"""
        self.loss = 0
        for i in range(STUDENTS_NUM):
            self.loss += self.get_student_loss(students[i], self.assignments[i])


    def swap_2_students(self, student1, student2):
        # check if the new assignments are valid
        if not students[student1].check_assignment(self.assignments[student2]) or not students[student2].check_assignment(self.assignments[student1]):
            return None
        
        new_assignment = Assigment()
        new_assignment.assignments = [a for a in self.assignments]
        new_assignment.assignments[student1], new_assignment.assignments[student2] = new_assignment.assignments[student2], new_assignment.assignments[student1]
        new_assignment.recalculate_loss()

        return new_assignment

    # return unique hash for the assignment
    def get_hash(self):
        return "#".join([str(a) for a in self.assignments])

    def get_all_neighbours(self, distance=2):
        if distance not in [1, 2]:
            raise NotImplementedError("Only distance 1,2 is supported")

        neighbours_hash = set()
        for i in range(0, STUDENTS_NUM):
            for j in range(1, STUDENTS_NUM):
                if i == j:
                    continue
                
                neighbour = self.swap_2_students(i, j)
                # check valid neighbour
                if neighbour is None:
                    continue
            
                h = neighbour.get_hash()
                if h in neighbours_hash:
                    continue

                neighbours_hash.add(h)
                yield neighbour

                if distance == 2:
                    for n in neighbour.get_all_neighbours(1):
                        h = n.get_hash()
                        if h in neighbours_hash:
                            continue
                        neighbours_hash.add(h)
                        yield n

    def get_best_neighbour(self):
        best_neighbour = None
        best_loss = self.loss
        for n in self.get_all_neighbours():        
            if n.loss < best_loss:
                best_loss = n.loss
                best_neighbour = n

        return best_neighbour
    

def summary(assignment):
    for i in range(PREFERENCE_NUM):
        print(f"Preference {i}:", [assignment.get_results()[s.id] == s.preferences[i] for s in students].count(True))

def get_best_random_assignment(cycles_num=1000):
    # Find one assignment that satisfies all constraints and minimizes the loss
    best_assignment = None
    min_loss = 100 * STUDENTS_NUM
    for cycle in range(0, cycles_num):
        #print(f"Cycle {cycle}...")

        assignment = Assigment()
        while assignment.loss < min_loss:
            unassigned_students = assignment.get_unassigned_students()
            #print("Unassigned students: ", unassigned_students)
            if len(unassigned_students) == 0:
                break

            student_id = random.choice(unassigned_students)
            student = students[student_id]
            groups = [group_id for group_id in range(GROUP_NUM) if assignment.check_assignment(student, group_id)]
            #print("Available groups: ", groups)
            if len(groups) == 0:
                # No group available for this student, assignment cannot be completed
                break

            group_id = random.choice(groups)
            assignment.assign(student, group_id)
            #print(f"Assigned student {student_id} to group {group_id} with loss {assignment.loss}")

        if len(assignment.get_unassigned_students())==0 and assignment.loss < min_loss:
            print(f"New best assignment found with loss {assignment.loss}")
            min_loss = assignment.loss
            best_assignment = assignment

    return best_assignment

def main():        
    ATTEMPTS_NUM = 10
    RANDOM_CYCLES_NUM = 1_000
    best_assignment = None
    start_time = datetime.now()
    
    for i in range(ATTEMPTS_NUM):
        print(f"Attempt {i}...")
        attempt_best_assignment = None
        assignment = get_best_random_assignment(RANDOM_CYCLES_NUM)
        if assignment is None:
            print(f"Attempt {i} failed")

        print("Initial assignment found with loss", assignment.loss)
        print("assignment", assignment) # XXX debug
        print("Attempting to improve the assignment...")
            
        best_neighbour = assignment.get_best_neighbour()
        while best_neighbour is not None:
            assignment = best_neighbour
            best_neighbour = assignment.get_best_neighbour()
            print(f"New neighbour assignment found with loss {assignment.loss}")

            attempt_best_assignment = assignment
            
        if attempt_best_assignment is None:
            print("Attempt to improve the assignment failed")
            attempt_best_assignment = assignment

        if best_assignment is None or attempt_best_assignment.loss < best_assignment.loss:
            best_assignment = attempt_best_assignment


    time_sec = (datetime.now() - start_time).total_seconds()
    print(f"Finished {ATTEMPTS_NUM} attempts of up to {RANDOM_CYCLES_NUM} random cycles cycles")
    print(f"Time taken: {time_sec} seconds")
    print(f"Average time per attempt: {time_sec/ATTEMPTS_NUM} seconds")
    print(f"Best assignment found with loss {best_assignment.loss}:\n{best_assignment}")
    summary(best_assignment)


if __name__ == "__main__":



    #cProfile.run('main()')
    main()