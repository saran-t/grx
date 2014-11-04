# GReXtension

*grx* is a macro processor intended to address the problem of writing index-heavy, numerical tensor code, in a compiler-friendly fashion.

## General principles and syntax

As far as possible, *grx* is designed to not collide with the syntax of languages commonly used in the field (for now this means C, C++ and Fortran). Unfortunately, this cannot be 100% achieved, as there are only so many keys on the keyboard, and the most of the remaining ones would result in weird and unsightly syntax that nobody ever wants to use. Ideally, the system should also require no knowledge whatsoever of the underlying language, but instead treating everything which is not part of its own syntax as simple blobs of text. Again, this might not always be possible.

### Tags

The main control directive used in *grx* is of the form

	@tag[[arg0, arg1, arg2, ...]]

- There **must not** be any space between `@` and `tag`, or between `tag` and `[[`.

- The list of arguments, including the brackets, may be omitted if the tag doesn't require it. 

- Some tags are *simple* and self-contained, while others are *extended* require an `@end` at the end of the block.

- The `@end` tag *optionally* accepts the name of the tag that it's meant to be closing, for example

		@iterate[[i, j=i..]] ...some text... @end
		@iterate[[i, j=i..]] ...some text... @end[[iterate]]

	are both valid. In the latter case, the parser would throw an error if the names don't match, providing an extra layer of safety. This is recommended when the block spans a large number of lines.

### Array expansion

The only control directive which is not an `@tag` is the array expansion. This is best explained by an example. When writing a 3D code we end up writing `f[x3][x2][x1]` a lot. In 11D this becomes `f[x11][x10]...[x1]` which is even worse. In *grx*, we can instead write

	f[[x#]]

- The system will generate the correct multidim-array syntax by iterating over `#`, specifically it will:

	- **(C/C++)** surround **each copy** of the inner string by `[...]` and replace `#` by numbers in **descending** order.

	- **(Fortran)** append a comma to **each copy** *apart from the last one*, run `#` in **ascending** order, then surround the **whole thing** by `(...)`

- In general, any `[[...]]` which does **not** immediately follow an `@tag` is treated as an array expansion.

- Note that the `#` may potentially collide with C preprocessor directives, but I hardly think that is a likely occurrence inside array indexes.

### Variables

At the end of the day, *grx* is a glorified macro substitution engine. To do this, it looks for some sort of tokens in the text and replace them by the value of some variables. In *grx*, these tokens take the form:

	`var`

or if we want to concatenate several variables:

	`mu`nu`rho`

- Variable names can consist of alphanumeric characters and underscores, and must not start with a digit.

- In general, the system looks for strings between pairs of `` `...` `` and checks whether it matches a variable name. If not it will leave the whole thing alone, including the `` ` ``.

- There is currently no way to generically define a variable in *grx*, however variables do get defined in iteration structures (see `@iterate`) and differentiation stencils (see `@stencil`).

### Caveats

- While the opening `[[` never appears in a valid C/C++ code, the closing `]]` ***can*** occur e.g. as in `x[y[i]]`. (I'm not sure about Fortran, someone can enlighten me.)

- For now, as *grx* doesn't parse anything that's not part of its control structure, `@tag[[x[y]]]` appears to the system as

	`@tag` `[[` first parameter `"x[y"` `]]` followed by the string `"]"`


	Likewise, commas could prove problematic, as `@tag[[f(x,y), z]]` appears as

	`@tag` `[[` first parameter `"f(x"` `,` second parameter `"y)"` `,` third parameter `" z"` `]]`

- Both of these issues can be rectified also inspecting various kinds of brackets in the parameter list. This somewhat violates the "no knowledge of underlying language" principle, but may well be required for usability. (The alternative would be, for example, to use `~` or `$` instead of `,` or `[[`, but I think that is taking things a little too far)

## Iteration

Iteration is the core functionality of *grx*. Unless stated otherwise, our examples assume that we are working in 3+1 GR so that ranges go from 1 to 3 by default. Also, any line breaks or tabs shown in the generated code are for illustrative purposes only: there is no reason to expect *grx* to actually beautify its generated code!

### Range specification

In the discussion below whenever we say `rangespec` we mean a string of the form

	i = imin .. imax

where:

- `i` must be a valid variable name which is *not* already declared in the current scope. This is called the **counter**.

- `imin` and `imax` are either non-negative integers or *previously declared* counters. Either or both of these *can* be omitted if `@defaultrange` is present (see below). For example, if we set `@defaultrange[[1,3]]` then `i = j..` is the same as `i = j..3`. This can be useful when dealing with symmetric tensors.

- When *both* `imin` and `imax` are omitted we can also drop the `=`. In other words, in 3+1 just write `i` instead of `i = ..` or `i = 1..3`.

- Whitespaces are entirely optional

---

### `@defaultrange`

#### Syntax
	
	@defaultrange[[ min, max ]]

#### Arguments

- `min` is a non-negative integer
- `max` is a non-negative integer

#### Explanation	
	
Sets the range for `[[...]]` array expansions, and also the default range used in `rangespecs`.

---

### `@iterate`

#### Syntax
	
	@iterate[[ range0, ... ]]
		block_of_text
	@end[[ iterate ]]

#### Arguments

- `range#` is a `rangespec`

#### Explanation

Repeats `block_of_text` according to `range#`. When multiple `rangespecs` are specified, `@iterate` behaves like a nested for-loop. For example:

	@iterate[[ i, j = i.. ]]
		const double A`i`j` = x`i` * y`j`;
	@end

produces

	const double A11 = x1 * y1;
	const double A12 = x1 * y2;
	const double A13 = x1 * y3;
	const double A22 = x2 * y2;
	const double A23 = x2 * y3;
	const double A33 = x3 * y3;

---

### `@expand`

#### Syntax
	
	@expand[[ some_text ]]

#### Arguments

- `some_text` is any string. Specially for this tag any `,` is treated as part of the string and **not** argument list delimiter.

#### Explanation

A simplified version of `@iterate` which does not require any `rangespec` or an `@end`. It behaves very similarly array expansions: it repeats `some_text` and each time replaces any `#` with numbers according to `@defaultrange`. The only difference is that it does not emit any extra brackets, commas, etc.

##### Example 1:

	@expand[[ for (int x# = 0; x# < len#; x#++) { ]]
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

##### Example 2:
	
	void f(const double *input @expand[[, int min#]] , @expand[[int max#, ]] double *output);

produces

	void f(const double *input, int min3, int min2, int min1, int max3, int max2, int max1, double *output);


#### Take note of:

- the order in which `#` runs -- this is the same as in array expansions, i.e. reversed in C and forward in Fortran.

- the various peculiar ways in which `,` appear in the second example -- the system doesn't know what you're trying to do, it just repeats things literally! 
	
# Substitution

At the moment, *grx* emits `#define` pragmas rather than actually performing string replacements itself. This is sufficient for e.g. defining symmetric components of a tensor. However, we improve upon it by allowing for these to be properly *scoped*, as explained below.

---

#### `@define`

#### Syntax
	
	@define[[ match, replace ]]

#### Arguments

- `match` is any string
- `replace` is any string

#### Explanation

When used inside a `@definescope`, emits `#define match replace` in the generated code. If `match` is identical to `replace` then it does nothing at all. For example:
	
	@iterate[[ i, j=i.. ]]
		@define[[g`j`i`, g`i`j`]]
	@end

produces

	#define g21 g12
	#define g31 g13
	#define g32 g23

Take care with commas appearing inside the arguments, though, as `@define[[f(x,y), x*y]]` yields an error: *grx* interprets this as having three arguments `f(x` and `y)` and `x*y`. This may have to be fixed at some point.

---

#### `@definescope`

#### Syntax
	
	@definescope
		block_of_text
	@end[[ definescope ]]

#### Arguments

- None

#### Explanation

Declares `block_of_text` to be within a `@definescope`. Each `@define` used within `block_of_text` will be logged internally, and at the `@end` it will emit an `#undef` for each `#define`. For example:
	
	void f() {
	@definescope
		@iterate[[ i, j=i.. ]]
			@define[[g`j`i`, g`i`j`]]
		@end

		some_code
	@end
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

#### `@stencil`

---

#### `@d1`

---

#### `@d2`






