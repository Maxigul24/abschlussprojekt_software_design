import numpy as np
import numpy.typing as npt

def solve(K: npt.NDArray[np.float64], F: npt.NDArray[np.float64], u_fixed_idx: list[int], eps=1e-9) -> npt.NDArray[np.float64] | None:
    """Solve the linear system Ku = F with fixed boundary conditions.

    Parameters
    ----------
    K : npt.NDArray[np.float64]
        Stiffness matrix.   
    F : npt.NDArray[np.float64]
        Force vector.
    u_fixed_idx : list[int]
        List of indices where the displacement is fixed (Dirichlet boundary conditions).
    eps : float, optional
        Regularization parameter to avoid singular matrix, by default 1e-9

    Returns
    -------
    npt.NDArray[np.float64] | None
        Displacement vector or None if the system is unsolvable.
    """

    assert K.shape[0] == K.shape[1], "Stiffness matrix K must be square."
    assert K.shape[0] == F.shape[0], "Force vector F must have the same size as K."

    K_calc = K.copy()
    F_calc = F.copy()

    for d in u_fixed_idx:       #Randbedingungen einbauen
        K_calc[d, :] = 0.0
        K_calc[:, d] = 0.0
        K_calc[d, d] = 1.0
        F_calc[d]=0.0

    try:
        u = np.linalg.solve(K_calc, F_calc) # solve the linear system Ku = F
        u[u_fixed_idx] = 0.0

        return u
    
    except np.linalg.LinAlgError:
        # If the stiffness matrix is singular we can try a small regularization to still get a solution
        K_calc += np.eye(K_calc.shape[0]) * eps

        try:
            u = np.linalg.solve(K_calc, F_calc) # solve the linear system Ku = F
            u[u_fixed_idx] = 0.0

            return u
        
        except np.linalg.LinAlgError:
            # If it is still singular we give up
            return None

def calc_single_stiffnesses(nodes: dict[int, tuple[float, float]], node_connections: list[tuple[int, int]]):

    K_o_dict = {}
    
    for (i, j) in node_connections:

        x_i, z_i = nodes[i]
        x_j, z_j = nodes[j]

        x_ji=x_j - x_i
        z_ji=z_j - z_i

        e_n = np.array([x_ji, z_ji])
        e_n = e_n / np.linalg.norm(e_n)

        laenge = np.sqrt(x_ji**2 + z_ji**2)

        if np.isclose(laenge, 1.0): #gleich wie ==1.0, aber mit Toleranz
            k=1.0
        else:
            k=1.0/np.sqrt(2)    #diagonal spring stiffness
        
        K = k * np.array([[1.0, -1.0], [-1.0, 1.0]])

        O_n = np.outer(e_n, e_n)

        Ko_n = np.kron(K, O_n)

        K_o_dict[(i, j)] = Ko_n
    
    return K_o_dict


def spring(nodes: dict[int, tuple[float, float]], node_connections: list[tuple[int, int]]) -> None:
    """Example of a spring system with 4 nodes and 6 spring elements.
    """
    Kg = np.zeros((2*len(nodes), 2*len(nodes))) # global stiffness matrix

    K_o_dict = calc_single_stiffnesses(nodes, node_connections)

    for (i, j), Ko_n in K_o_dict.items():
        # Die 4 relevanten Indizes (Freiheitsgrade) bestimmen [cite: 153]
        dofs = [2*i, 2*i+1, 2*j, 2*j+1]
        
        Kg[np.ix_(dofs, dofs)] += Ko_n  # Eintragen in die globale Steifigkeitsmatrix am richtigen Ort
        #ist das gleiche wie zuvor die beiden for-schleifen

    
    print(f"{Kg=}")

    u_fixed_idx = [0, 1] # fix node i in both directions

    F = np.array([0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0]) # apply force at node j in x-direction

    u = solve(Kg, F, u_fixed_idx)
    print(f"{u=}")


if __name__ == "__main__":

    nodes=dict()
    nodes={
        0: (0.0, 0.0),
        1: (1.0, 0.0),
        2: (0.0, 1.0),
        3: (1.0, 1.0)
    }

    node_connections = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3)]
    
    spring(nodes, node_connections)