# GReXtension

*grx* is a macro processor, primarily intended to ease the writing of good code for General Relativity simulations. These numerical tensor codes are very heavy on indices, leading to rather messy code which is often not amenable to straightforward compiler optimization without causing even further mess.

To demonstrate the point, let us consider writing code to calculate the spatial Christoffel symbols in C99:
	
	#define DIM 3
	double Gamma[DIM][DIM][DIM];

	for (int i = 1; i < DIM; i++) {
		for (int j = 1; j < DIM; j++) {

			// Christoffel symbols are symmetric in the lower two indices
			for (int k = j; k < DIM; k++) {
				Gamma[i][j][k] = 0.;

				for (int l = 0; l < DIM; l++) {
					// dg an ginv are precalculated elsewhere
					Gamma[i][j][k] += 0.5 * ginv[i][l] * (dg[j][l][k] + dg[k][l][j] - dg[j][k][l]);
				}
				
				Gamma[i][k][j] = Gamma[i][j][k];
			}

		}
	}

A few noteworthy issues here include:
	
- Tensors have indices that range up to #(spacetime dimensions) *by default*, yet we have to explicitly state this at every loop. 

- In all likelihood, such a loop appears inside a larger, outer loop ranging over the grid points in our domain. This outer loop should really be vectorizable by the compiler. By declaring `Gamma` as an array, the compiler is unlikely to fully vectorize the calculations. If we declare and calculate each component as a separate variable, the code would become trivially vectorizable.

- Just because we have assigned `Gamma[i][k][j] = Gamma[i][j][k]` does not mean that the compiler necessarily realises that these are the same quantity. Ideally we want to `#define` these two components in order to make the symmetry explicit, however we cannot do this in the loop.

- We could manually write out the calculation of each component and all the `#define`. We would then want to `#undef` everything at the end of the function as well for safety. This is obviously prone to human error and it will be impossible to change or maintain the resulting code.

- All of the above points get amplified when we realise that the loop written above is just one of many that occurs in real simulation code.

- Then there is the calculation of finite difference derivatives of 10 tensors. With up to four stencils each. In 11 dimensions.

Using *grx* we can produce readable code with all of these improvements:

	@defaultrange[[1,3]]
	@definescope

	@iterate[[i, j, k=j..]]
		const double Gamma`i`j`k` = 0.5 * @sum[[l]] ginv`i`l` * (dg`j`l`k` + dg`k`l`j` - dg`j`k`l`) @end;
		@define[[Gamma`i`k`j`, Gamma`i`j`k`]]
	@end

	@end[[definescope]]


## General principles and syntax

As far as possible, *grx* is designed to not collide with the syntax of languages commonly used in the field (for now this means C, C++ and Fortran). Unfortunately, this cannot be 100% achieved, as there are only so many keys on the keyboard, and the most of the remaining ones would result in strange and unsightly syntax. Ideally, the system should also require no knowledge whatsoever of the underlying language: it should just treat anything which is not part of its own syntax as simple blobs of text. 

*grx* is conceptually inspired by **Chombo Fortran**, which aims to help people write dimension-independent Fortran code. *grx* extends this concept further by introducing more general macro directives and also removes the specific dependence on Fortran.

### Tags

The main control directive used in *grx* is of the form

	@tag[[arg0, arg1, arg2, ...]]

- There **must not** be any space between `@` and `tag`, or between `tag` and `[[`.

- The list of arguments, including the brackets, may be omitted if the tag doesn't require it. 

- A number of tags define a *block* which requires an `@end` to close off. The `@end` tag *optionally* accepts the name of the tag that it's meant to be closing, for example

		@iterate[[i, j=i..]] block_of_text @end
		@iterate[[i, j=i..]] block_of_text @end[[iterate]]

	are both valid. In the latter case, the parser would throw an error if the names don't match, providing an extra layer of safety. This is recommended when the block spans a large number of lines.

- According to Wikipedia, our use of `@` makes *grx* incompatible with Objective-C, Swift, Ruby, Python, Java, C#, Haskell, and many other languages. This is unfortunate, however it does mean that search engines might pick up keywords from the above list.

### Array expansions

The only control directive which is not an `@tag` is the **array expansion**. This is best explained by an example. When writing a 3D code we end up writing `f[x3][x2][x1]` a lot. In 11D this becomes `f[x11][x10]...[x1]` which is even worse. In *grx*, we can instead write

	f[[x#]]

- The system will generate the correct syntax for multidimensional arrays, by producing multiple copies of the enclosed string and then:

	- **(C/C++)** surround **each copy** of the inner string by `[...]` and replace any `#` by numbers in **descending** order.

	- **(Fortran - to be implemented)** append a comma to **each copy** *apart from the last one*, run `#` in **ascending** order, then surround the **whole thing** by `(...)`

- The number of copies generated is governed by `@defaultrange` (discussed later)

- In general, any `[[...]]` which does **not** immediately follow an `@tag` is treated as an array expansion.

- Note that the use of `#` may potentially collide with C preprocessor directives, but I hardly think that is a likely occurrence inside array indexes.

### Variables

At the end of the day, *grx* is a glorified macro substitution engine. To do this, it looks for some sort of tokens in the text and replace them by the value of some variables. In *grx*, these tokens take the form:

	`var`

or if we want to concatenate several variables:

	`mu`nu`rho`

- Variable names can consist of alphanumeric characters and underscores, and must start with a letter.

- In general, the system looks for strings between pairs of `` `...` `` and checks whether it matches a variable name. If not it will leave the whole thing alone, including the `` ` ``.

- There is currently no way to explicitly assign a value to a variable in *grx*. Instead, variables get defined through certain specific tags (for example, in `@iterate`)

## Iteration

*grx* offers several iteration macros at different levels of compromise between brevity and flexibility.

Unless stated otherwise, our examples assume that we are working with 3+1 GR so that ranges go from 1 to 3 by default. Also, any line breaks or tabs shown in the generated code are for illustrative purposes only: *grx* does *not* beautify its generated code!

---

### `@defaultrange`

#### Syntax
	
	@defaultrange[[ min, max ]]

#### Arguments

- `min` is a non-negative integer
- `max` is a non-negative integer

#### Explanation	
	
Sets the iteration range which is used by default, unless otherwise overridden by a `rangespec` (see `@iterate`).

#### Example

For 3+1 GR, the canonical choice for spatial quantities would be:

	@defaultrange[[1, 3]]

---

### `@expand` and `@rexpand`

#### Syntax
	
	@expand[[ some_text ]]

and 

	@rexpand[[ some_text ]]

#### Arguments

- `some_text` is any string.

#### Explanation

The simplest iteration macro in *grx*: `some_text` is repeated verbatim, except each time any `#` that appears in `some_text` is replaced by a number which is incremented (for `@expand`) or decremented (for `@rexpand` i.e. *reversed expand*) according to `@defaultrange`.

#### Example 1

Expanding out lower and upper bound variables for a 3D array -- the horrible way:
	
	void f(const double *input @expand[[, int min#]] , @expand[[int max#, ]] double *output);

produces

	void f(const double *input, int min1, int min2, int min3, int max1, int max2, int max3, double *output);

Take note of the various peculiar ways in which `,` appear here: *grx* doesn't know what you're trying to do, it just repeats things literally!

In fact, for this particular example we should have used `@argexpand` (see below).

#### Example 2

A for-loop is a typical use case for reversed expansion:

	@rexpand[[ for (int x# = 0; x# < len#; x#++) { ]]
		some_code
	@expand[[ } ]]

produces

	for (int x3 = 0; x3 < len3; x3++) {
		for (int x2 = 0; x2 < len2; x2++) {
			for (int x1 = 0; x1 < len1; x1++) {
				some_code
			}
		}
	}

---

### `@argexpand`

#### Syntax
	
	@argexpand[[ some_text ]]

#### Arguments

- `some_text` is any string.

#### Explanation

Like `@expand` but also inserts `,` *between* copies of `some_text`. Intended for use in function arguments.

#### Example

We can rewrite Example 1 for `@expand` in a more sensible manner:
	
	void f(const double *input, @argexpand[[int min#]], @argexpand[[int max#]], double *output);

also produces

	void f(const double *input, int min1, int min2, int min3, int max1, int max2, int max3, double *output);

#### Example 2

A for-loop is a typical use case for reversed expansion:

	@rexpand[[ for (int x# = 0; x# < len#; x#++) { ]]
		some_code
	@expand[[ } ]]

produces

	for (int x3 = 0; x3 < len3; x3++) {
		for (int x2 = 0; x2 < len2; x2++) {
			for (int x1 = 0; x1 < len1; x1++) {
				some_code
			}
		}
	}

---

### `@iterate`

#### Syntax
	
	@iterate[[ range0, range1, range2, ... ]]
		block_of_text
	@end[[ iterate ]]

#### Arguments

- each `range#` is a `rangespec`, i.e. a *range specification string* of the form

		i = imin .. imax

where:

- `i` is a valid variable name which is *not* already declared in the current scope. This is called the **counter**. This causes `i` to be declared as a new variable, so that any `` `i` `` appearing in `block_of_text` gets replaced by the current value of `i`.

- `imin` and `imax` are either non-negative integers or *previously declared* counters. If `@defaultrange` is present then either or both of these *can* be omitted. For example, if we set `@defaultrange[[1,3]]` then `i=j..` is the same as `i=j..3`.

- When *both* `imin` and `imax` are omitted we can also drop the `=`. In other words, we can just use `i` instead of `i=..` or `i=1..3`.

- Whitespaces are entirely optional

#### Explanation

The main iteration macro in *grx* which is much more flexible than `@expand`. It repeats `block_of_text` according to the specified `range#`. Where multiple `range#` are specified, `@iterate` behaves like a nested loop.

#### Example

Vector outer product:

	@iterate[[ i, j=i.. ]]
		const double A`i`j` = x`i` * y`j`;
	@end

is equivalent to

	@iterate[[ i ]]
		@iterate[[ j=i.. ]]
			const double A`i`j` = x`i` * y`j`;
		@end
	@end

which produces

	const double A11 = x1 * y1;
	const double A12 = x1 * y2;
	const double A13 = x1 * y3;
	const double A22 = x2 * y2;
	const double A23 = x2 * y3;
	const double A33 = x3 * y3;

---

### `@sum`

#### Syntax
	
	@sum[[ range0, range1, range2, ... ]]
		block_of_text
	@end[[ sum ]]

#### Arguments

- each `range#` is a `rangespec` (see `@iterate` above for details)

#### Explanation

Does everything that `@iterate` does, but also:

- Inserts `(...)` around **each copy** of `block_of_text`
- Inserts a `+` in between each copy
- Surrounds the **entire output** by another pair of `(...)`

This means that we can *safely* generate a summation expression without having to worry about the parentheses.

#### Example

Vector inner product, with metric -k*g<sub>μν</sub>:

	const double B = k * @sum[[mu,nu]] -g`mu`nu` * x`mu` * y`nu` @end;

produces

	const double B = k * ( 
		((-g11 * x1 * y1) + (-g12 * x1 * y2) + (-g13 * x1 * y3)) + 
		((-g21 * x2 * y1) + (-g22 * x2 * y2) + (-g23 * x2 * y3)) +
		((-g31 * x3 * y1) + (-g32 * x3 * y2) + (-g33 * x3 * y3))
	);


# Substitution

At the moment, *grx* emits `#define` pragmas rather than actually performing string replacements itself. This is sufficient for e.g. defining symmetric components of a tensor. However, we do improve upon it by allowing for these to be properly *scoped*, as explained below.

---

#### `@define`

#### Syntax
	
	@define[[ match, replace ]]

#### Arguments

- `match` is any string
- `replace` is any string

#### Explanation

When used inside a `@definescope`, emits `#define match replace` in the generated code. If `match` is identical to `replace` then it does nothing at all.

#### Example

Symmetry of the metric tensor:
	
	@iterate[[ i, j=i.. ]]
		@define[[g`j`i`, g`i`j`]]
	@end

produces

	#define g21 g12
	#define g31 g13
	#define g32 g23

#### Caution

Take care with commas appearing inside the arguments. At the moment `@define[[f(x,y), x*y]]` yields an error because *grx* interprets this as having three arguments `f(x` and `y)` and `x*y`. This will be fixed eventually.

---

#### `@definescope`

#### Syntax
	
	@definescope
		block_of_text
	@end[[ definescope ]]

#### Arguments

- None

#### Explanation

Declares `block_of_text` to be within a `@definescope`. Each `@define` used within `block_of_text` is logged internally, and at the `@end` it will emit an `#undef` for each `#define`. 

#### Example

	void f() {
	@definescope

		@iterate[[ i, j=i.. ]]
			@define[[g`j`i`, g`i`j`]]
		@end[[iterate]]

		some_code

	@end[[definescope]]
	}

produces

	void f() {
		#define g21 g12
		#define g31 g13
		#define g32 g23

		some_code

		#undef g21
		#undef g31
		#undef g32
	}

# Differentiation

Writing finite differences code in multiple dimensions is often prone to errors. Higher order differentiation is even more problematic as a different stencils must be used for repeated partials and mixed partials. *grx* provides a number of macros to help in this area.

#### `@stencil`

### Syntax
	
	@stencil[[ stencilname ]]
		@points[[  point0,  ..., pointN  ]]
		@weights[[ weight0, ..., weightN ]]
	@end[[ stencil ]]

#### Arguments

- `stencilname` is a valid variable name, to be used as the name of this stencil
- `point#` is any string
- `weight#` is any string

#### Explanation

Defines a stencil with the name `stencilname`, to be used by derivative code generation macros. The stencil assigns the weight `weight#` to the point shifted by `point#` from the current location. Both `@points` and `@weights`, with the same number of arguments, are required for the `@stencil` block to be valid. Note that the arguments of `@points` and `@weights` are reproduced verbatim: *grx* will not convert them to integers or floating points or anything else. This tag does not produce any text in the output.

#### Example 1

1<sup>st</sup> derivative using 4<sup>th</sup> order central difference:
	
	@stencil[[d1cen4]]
		@points[[  -2,    -1,     1,     2      ]]
		@weights[[ 1/12., -8/12., 8/12., -1/12. ]]
	@end

Note that we have to add trailing dots to the weights in order to make sure that floating point division is used, otherwise the C/Fortran compiler will treat them as zeroes!

#### Example 2

2<sup>nd</sup> derivative using 4<sup>th</sup> order central difference:
	
	@stencil[[d2cen4]]
		@points[[  -2,     -1,     0,       1,      2      ]]
		@weights[[ -1/12., 16/12., -30/12., 16/12., -1/12. ]]
	@end

---

#### `@d1`

### Syntax
	
	@d1[[ f, i, stencil ]]

#### Arguments

- `f` is any string, typically containing an `[[...]]` array expansion token
- `i` is either a non-negative integer or a previously declared numerical variable
- `stencil` is the name of a previously defined `@stencil`

#### Explanation

Generates code for the first derivative ∂f/∂x<sup>i</sup>, using the stencil defined by `stencil`. Plenty of parentheses are around everything in the process in order to ensure that minus signs, etc. are translated correctly. I could explain exactly what the macro does, but it's probably easier to just look at the examples.

#### Example 1

Differentiating a scalar function using the stencil `d1cen4` from Example 1 for `@stencil`:
	
	const double f[x3size][x2size][x1size];	// f is a scalar function
	const double dx;	// dx is the grid spacing

	@iterate[[ i ]]
		const double df`i = @d1[[ f[[x#]], i, d1cen4 ]] / dx;
	@end

produces
	
	const double df1 = ((1/12.) * (f[(x3)][(x2)][(x1) + (-2)]) + (-8/12.) * (f[(x3)][(x2)][(x1) + (-1)]) + (8/12.) * (f[(x3)][(x2)][(x1) + (1)]) + (-1/12.) * (f[(x3)][(x2)][(x1) + (2)])) / dx;
	const double df2 = ((1/12.) * (f[(x3)][(x2) + (-2)][(x1)]) + (-8/12.) * (f[(x3)][(x2) + (-1)][(x1)]) + (8/12.) * (f[(x3)][(x2) + (1)][(x1)]) + (-1/12.) * (f[(x3)][(x2) + (2)][(x1)])) / dx;
	const double df3 = ((1/12.) * (f[(x3) + (-2)][(x2)][(x1)]) + (-8/12.) * (f[(x3) + (-1)][(x2)][(x1)]) + (8/12.) * (f[(x3) + (1)][(x2)][(x1)]) + (-1/12.) * (f[(x3) + (2)][(x2)][(x1)])) / dx;

which, without the *"paranoid parantheses"*, is roughly equivalent to *(ignoring the quirks of rearranging floating point operations)*
	
	const double df1 = (f[x3][x2][x1-2] - 8. * f[x3][x2][x1-1] + 8. * f[x3][x2][x1+1] - f[x3][x2][x1+2]) / (12. * dx);
	const double df2 = (f[x3][x2-2][x1] - 8. * f[x3][x2-1][x1] + 8. * f[x3][x2+1][x1] - f[x3][x2+2][x1]) / (12. * dx);
	const double df3 = (f[x3-2][x2][x1] - 8. * f[x3-1][x2][x1] + 8. * f[x3+1][x2][x1] - f[x3+2][x2][x1]) / (12. * dx);

#### Example 2

We can similarly differentiate a tensor by using `@iterate` in the obvious way:
	
	@iterate[[ i, j=i.., k ]]
		const double dg`i`j`k` = @d1[[ g`i`j`[[x#]] / dx, k, d1cen4 ]];
		@define[[ dg`j`i`k`, dg`i`j`k` ]]
	@end

produces exactly what you think it should.

---

#### `@d2`

### Syntax
	
	@d2[[ f, i, j, stencil1, stencil2 ]]

#### Arguments

- `f` is any string, typically containing an `[[...]]` array expansion token
- `i` and `j` are either a non-negative integers or a previously declared numerical variables
- `stencil1` and `stencil2` are the names of a previously defined `@stencil`

#### Explanation

Generates code for the second derivatives ∂<sup>2</sup>f/(∂x<sup>i</sup>∂x<sup>j</sup>). For mixed derivatives (i.e. off-diagonal terms in the Hessian) `stencil1` is used to calculate the first derivative in each direction, while for repeated derivatives (i.e. diagonal terms in the Hessian) `stencil2` is used to calculate the second derivative. Like `@d1` this macro produces plenty of parentheses.

#### Example

Differentiating a scalar function twice:
	
	@iterate[[ i, j=i.. ]]
		const double ddf`i`j` = @d2[[ f[[x#]], i, j, d1cen4, d2cen4 ]] / (dx * dx);
	@end

produces parentheses-filled code which is equivalent to
	
	const double ddf11 = (
		- f[x3][x2][x1-2] + 16. * f[x3][x2][x1-1] - 30. * f[x3][x2][x1] + 16. * f[x3][x2][x1+1] - f[x3][x2][x1+2]
	) / (12. * dx * dx);
	
	const double ddf12 = (
		       f[x3][x2-2][x1-2] -  8. * f[x3][x2-2][x1-1] +  8. * f[x3][x2-2][x1+1] -      f[x3][x2-2][x1+2]
		- 8. * f[x3][x2-1][x2-2] + 64. * f[x3][x2-1][x1-1] - 64. * f[x3][x2-1][x1+1] + 8. * f[x3][x2-1][x1+2]
		+ 8. * f[x3][x2+1][x2-2] - 64. * f[x3][x2+1][x1-1] + 64. * f[x3][x2+1][x1+1] - 8. * f[x3][x2+1][x1+2]
		-	   f[x3][x2+2][x1-2] +  8. * f[x3][x2+2][x1-1] -  8. * f[x3][x2+2][x1+1] +      f[x3][x2+2][x1+2]
	) / (144. * dx * dx);

	and so on...

Check out the example for `@d1` to see exactly how *grx* inserts parentheses into derivative expressions.

---

## General caveats

Here is a list of things which may cause unexpected behaviour in *grx*. I hope to fix most of these once I figure out a good solution for them.

- While the opening `[[` never appears in a valid C/C++ code, the closing `]]` ***can*** occur e.g. as in `x[y[i]]`. (I'm not sure about Fortran, someone can enlighten me.)

- For now, as *grx* doesn't parse anything that's not part of its control structure, `@tag[[x[y]]]` appears to the system as

	`@tag` `[[` first parameter `"x[y"` `]]` followed by the string `"]"`


	Likewise, commas could prove problematic, as `@tag[[f(x,y), z]]` appears as

	`@tag` `[[` first parameter `"f(x"` `,` second parameter `"y)"` `,` third parameter `" z"` `]]`

	The "comma problem" does not apply to `@expand`, `@rexpand` and `@argexpand` as these tags are programmed specifically to ignore `,`.

- Both of these issues can be fixed by also inspecting various kinds of brackets in the parameter list. This somewhat violates the "no knowledge of underlying language" principle, but may well be required for usability. (The alternative would be, for example, to use `~` or `$` instead of `,` or `[[`, but I think that is taking things a little too far)



