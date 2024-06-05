import numpy as np

import streamlit as st

st.set_page_config(page_title='Transportation Problem Solver')

#handling degeneracy
def handle_degeneracy(allocation):
    rows,col=allocation.shape
    num_allocations = np.count_nonzero(allocation)
    if num_allocations < rows+col-1:
        for i in range(rows):
            for j in range(col):
                if allocation[i,j] == 0:
                    allocation[i,j] == 1e-5 #assigning epilson value
                    if np.count_nonzero(allocation)==rows+col-1:
                        return allocation
    return allocation

#calculating u and v
def calculate_u_v(cost, allocation):
    rows, cols = cost.shape
    u = np.full(rows, None)
    v = np.full(cols, None)
    u[0] = 0
    
    while any(u is None for u in u) or any(v is None for v in v):
        for i in range(rows):
            for j in range(cols):
                if allocation[i, j] > 0:
                    if u[i] is not None and v[j] is None:
                        v[j] = cost[i, j] - u[i]
                    elif v[j] is not None and u[i] is None:
                        u[i] = cost[i, j] - v[j]
    return u, v


#calculating opportunity cost
def check_optimality(cost, u, v):
    rows, cols = cost.shape
    delta = np.zeros((rows, cols), dtype=int)
    for i in range(rows):
        for j in range(cols):
            delta[i, j] = cost[i, j] - (u[i] + v[j])
    return delta

#selecting the cell with negative opportunity cost
def find_entering_variable(delta):
    min_value = np.min(delta)
    if min_value < 0:
        return np.unravel_index(np.argmin(delta), delta.shape)
    else:
        return None


#looping
def identify_loop(allocation, start):

    rows, col = allocation.shape
    allocated_cells = list(zip(*np.where(allocation > 0)))
    visited = set()

    def loop_search(current_path, current_direction):
        last_cell = current_path[-1]
        visited.add(last_cell)
        candidates = []

        if current_direction == 'horizontal':
            candidates = [(last_cell[0], j) for j in range(col) if (last_cell[0], j) != last_cell]
        elif current_direction == 'vertical':
            candidates = [(i, last_cell[1]) for i in range(col) if (i, last_cell[1]) != last_cell]

        for cell in candidates:
            if cell in allocated_cells and cell not in visited:
                new_path = current_path.copy()
                new_path.append(cell)

                if len(new_path) >= 4 and (new_path[0][0] == new_path[-1][0] or new_path[0][1] == new_path[-1][1]):
                    # Check if the loop is formed with the correct sequence of horizontal and vertical moves
                    valid_loop = True
                    for idx in range(len(new_path) - 2):
                        if (new_path[idx][0] == new_path[idx + 1][0]) == (new_path[idx + 1][0] == new_path[idx + 2][0]):
                            valid_loop = False
                            break

                    if valid_loop:
                        return new_path

                alternate_direction = 'horizontal' if current_direction == 'vertical' else 'vertical'
                result = loop_search(new_path, alternate_direction)
                if result:
                    return result
        visited.remove(last_cell)
        return None

    loop = loop_search([start], 'horizontal') or loop_search([start], 'vertical')
    if loop:
        loop = [loop[i] if i % 2 == 0 else loop[-(i % len(loop))] for i in range(len(loop))]
    return loop



#assigning new allocations based on the loop
def adjust_allocation(allocation, cycle, entering):
    min_allocation = min(allocation[i, j] for i, j in cycle[1::2])
    for k in range(0, len(cycle), 2):
        allocation[cycle[k]] += min_allocation
    for k in range(1, len(cycle), 2):
        allocation[cycle[k]] -= min_allocation
    return allocation

#the combination of all above functions
def modi_method(cost, allocation):
    allocation = handle_degeneracy(allocation)
    while True:
        u, v = calculate_u_v(cost, allocation)
        delta = check_optimality(cost, u, v)
        entering = find_entering_variable(delta)
        if entering is None:
            break
        cycle = identify_loop(allocation, entering)
        allocation = adjust_allocation(allocation, cycle, entering)
        allocation = handle_degeneracy(allocation)
    total_cost = np.sum(allocation*cost)
    return allocation, total_cost


#for user input
def input_matrix(rows, cols, matrix_name):
    st.write(f"Enter the {matrix_name} matrix ({rows}x{cols}):")
    matrix = []
    for i in range(rows):
        row = st.text_input(f"Row {i + 1}:", key=f"{matrix_name}_row_{i}")
        if row:  # Check if row input is provided
            try:
                row_values = list(map(int, row.split()))
                if len(row_values) != cols:
                    st.error(f"Row {i + 1} must have exactly {cols} values.")
                    #return None
                matrix.append(row_values)
            except ValueError:
                st.error(f"Invalid input in Row {i + 1}. Please enter {cols} integer values separated by spaces.")
                #return None
        else:
            st.error(f"Row {i + 1} is required.")
            #return None

    return np.array(matrix)

#main function
def main():
    st.markdown("""# Transportation Problem Solver
**You should have an initial feasible solution (cost and initial allocation) on hand. This program will provide you with the optimal solution. The program is limited to four sources and destinations**
   """)
    rows = int(st.number_input("Enter the number of rows in the cost matrix: ", step=1, min_value=3))
    cols = int(st.number_input("Enter the number of columns in the cost matrix: ", step=1, min_value=3))

    if (rows > 4) or (cols > 4): #to limit the program to 4 sources and destinations
        st.warning("Oops! Sorry, this program is limited to 4 sources and destinations.")
    else:
        #to enter the cost matrix
        cost = input_matrix(rows, cols, "cost")
        #to enter the allocation matrix
        initial_allocation = input_matrix(rows, cols, "initial_allocation")

        if st.button("Generate Optimal Solution"):
            
            try:
                optimal_allocation, total_cost = modi_method(cost, initial_allocation)
            except ValueError:
                st.error("You did not enter appropriate values")
            st.success("Here is your optimal transportation route with the associated total cost")
            st.write("Optimal Allocation : \n", optimal_allocation)
            st.write("Total Cost: ", total_cost)


if __name__ == "__main__":
    main()
