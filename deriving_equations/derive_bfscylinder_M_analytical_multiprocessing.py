"""
Deriving structural matrices for BFS plate finite element
Using multiprocessing to accelerate the symbolic integrations
"""
from multiprocessing import Pool
import numpy as np
import sympy

cpu_count = 6
DOF = 6

def integrate_simplify(integrand):
    return sympy.simplify(sympy.integrate(integrand, ('xi', -1, 1), ('eta', -1, 1)))

def main():
    sympy.var('xi, eta, lex, ley, rho, h')
    sympy.var('A11, A12, A16, A22, A26, A66')
    sympy.var('B11, B12, B16, B22, B26, B66')
    sympy.var('D11, D12, D16, D22, D26, D66')

    ONE = sympy.Integer(1)

    # shape functions
    # - from Reference:
    #     OCHOA, O. O.; REDDY, J. N. Finite Element Analysis of Composite Laminates. Dordrecht: Springer, 1992.
    # bi-linear
    Li = lambda xii, etai: ONE/4.*(1 + xi*xii)*(1 + eta*etai)
    # cubic
    Hwi = lambda xii, etai: ONE/16.*(xi + xii)**2*(xi*xii - 2)*(eta+etai)**2*(eta*etai - 2)
    Hwxi = lambda xii, etai: -lex/32.*xii*(xi + xii)**2*(xi*xii - 1)*(eta + etai)**2*(eta*etai - 2)
    Hwyi = lambda xii, etai: -ley/32.*(xi + xii)**2*(xi*xii - 2)*etai*(eta + etai)**2*(eta*etai - 1)
    Hwxyi = lambda xii, etai: lex*ley/64.*xii*(xi + xii)**2*(xi*xii - 1)*etai*(eta + etai)**2*(eta*etai - 1)

    # node 1 (-1, -1)
    # node 2 (+1, -1)
    # node 3 (+1, +1)
    # node 4 (-1, +1)

    Nu = sympy.Matrix([[
        Li(-1, -1), 0, 0, 0, 0, 0,
        Li(+1, -1), 0, 0, 0, 0, 0,
        Li(+1, +1), 0, 0, 0, 0, 0,
        Li(-1, +1), 0, 0, 0, 0, 0,
        ]])
    Nv = sympy.Matrix([[
        0, Li(-1, -1), 0, 0, 0, 0,
        0, Li(+1, -1), 0, 0, 0, 0,
        0, Li(+1, +1), 0, 0, 0, 0,
        0, Li(-1, +1), 0, 0, 0, 0,
        ]])
    Nw = sympy.Matrix([[
       #u, v, w,     , dw/dx  , dw/dy,  d2w/(dxdy)
        0, 0, Hwi(-1, -1), Hwxi(-1, -1), Hwyi(-1, -1), Hwxyi(-1, -1),
        0, 0, Hwi(+1, -1), Hwxi(+1, -1), Hwyi(+1, -1), Hwxyi(+1, -1),
        0, 0, Hwi(+1, +1), Hwxi(+1, +1), Hwyi(+1, +1), Hwxyi(+1, +1),
        0, 0, Hwi(-1, +1), Hwxi(-1, +1), Hwyi(-1, +1), Hwxyi(-1, +1),
        ]])
    A = sympy.Matrix([
        [A11, A12, A16],
        [A12, A22, A26],
        [A16, A26, A66]])
    B = sympy.Matrix([
        [B11, B12, B16],
        [B12, B22, B26],
        [B16, B26, B66]])
    D = sympy.Matrix([
        [D11, D12, D16],
        [D12, D22, D26],
        [D16, D26, D66]])

    # bending
    Nphix = -(2/lex)*Nw.diff(xi)
    Nphiy = -(2/ley)*Nw.diff(eta)

    # integrating matrices in natural coordinates
    #TODO integrate only upper or lower triangle

    print('Integrating Me')
    integrands = []
    for ind, integrand in np.ndenumerate(Me):
        integrands.append(integrand)
    p = Pool(cpu_count)
    a = list(p.map(integrate_simplify, integrands))
    for i, (ind, integrand) in enumerate(np.ndenumerate(Me)):
        Me[ind] = a[i]

    # M represents the global mass matrix
    # in case we want to apply coordinate transformations
    M = Me

    def name_ind(i):
        if i >=0 and i < DOF:
            return 'c1'
        elif i >= DOF and i < 2*DOF:
            return 'c2'
        elif i >= 2*DOF and i < 3*DOF:
            return 'c3'
        elif i >= 3*DOF and i < 4*DOF:
            return 'c4'
        else:
            raise

    print('printing for code')
    for ind, val in np.ndenumerate(M):
        if val == 0:
            continue
        i, j = ind
        si = name_ind(i)
        sj = name_ind(j)
        print('        M[%d+%s, %d+%s]' % (i%DOF, si, j%DOF, sj), '+=', M[ind])

    #TODO mass matrix

if __name__ == '__main__':
    main()
