import random
import cProfile
from datetime import datetime

STUDENTS_NUM = 70
GROUP_NUM = 7
GROUP_SIZE = 10

def rand_bool(probability=0.5):
    return random.random() < probability

class Student:
    def __init__(self, id, constraint_prob=0.5, preferences_num=3):
        self.id = id
        self.constraints = [rand_bool(constraint_prob) for i in range(0, GROUP_NUM)]
        self.preferences = []
        possible_preferences = set(range(0, GROUP_NUM))
        for i in range(0, preferences_num):
            choise = random.choice(list(possible_preferences))
            self.preferences.append(choise)
            possible_preferences.remove(choise)

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

    def get_all_neighbours(self):
        for i in range(0, STUDENTS_NUM):
            for j in range(1, STUDENTS_NUM):
                if i == j:
                    continue
                
                neighbour = self.swap_2_students(i, j)
                # check valid neighbour
                if neighbour is None:
                    continue
            
                yield neighbour

    def get_best_neighbour(self):
        best_neighbour = None
        best_loss = self.loss
        for n in self.get_all_neighbours():        
            if n.loss < best_loss:
                best_loss = n.loss
                best_neighbour = n

        return best_neighbour
    
def main():        

    CYCLE_NUM = 100_000
    min_loss = 100 * STUDENTS_NUM
    best_assignment = None
    start_time = datetime.now()
    last_improvement_time = None

    for cycle in range(0, CYCLE_NUM):
        #print(f"Cycle {cycle}...")

        # Find one assignment that satisfies all constraints and minimizes the loss
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

            print("New best assignment found, checking its neighbours...")
            if True:
                best_neighbour = assignment.get_best_neighbour()
                while best_neighbour is not None:
                    assignment = best_neighbour
                    best_neighbour = assignment.get_best_neighbour()
                    print(f"New best assignment found with loss {assignment.loss}")

            improvement = min_loss - assignment.loss
            min_loss = assignment.loss
            best_assignment = assignment
            print(f"New best assignment found with loss {min_loss}")
            if last_improvement_time is not None:
                try:
                    print(f"Improvement rate (per second): {improvement / (datetime.now() - last_improvement_time).total_seconds()}")
                except ZeroDivisionError:
                    # this is fine for the initial phase of the algorithm when many imrpovements are made in a short time
                    pass
            last_improvement_time = datetime.now()


    time_sec = (datetime.now() - start_time).total_seconds()
    print(f"Finished {CYCLE_NUM} cycles")
    print(f"Time taken: {time_sec} seconds")
    print(f"Average time per cycle: {time_sec/CYCLE_NUM} seconds")
    print(f"Best assignment found with loss {min_loss}:\n{best_assignment}")

if __name__ == "__main__":
    #cProfile.run('main()')
    main()