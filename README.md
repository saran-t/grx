# GReXtension

*grx* is a macro processor intended to address the problem of writing index-heavy, numerical tensor code, in a compiler-friendly fashion.

## General principles and syntax

As far as possible, *grx* is designed to not collide with the syntax of languages commonly used in the field (for now this means C, C++ and Fortran). Unfortunately, this cannot be 100% achieved, as there are only so many keys on the keyboard, and the most of the remaining ones would result in weird and unsightly syntax that nobody ever wants to use. Ideally, the system should also require no knowledge whatsoever of the underlying language, but instead treating everything which is not part of its own syntax as simple blobs of text. Again, this might not always be possible.

### Tags

The main control directive used in *grx* is of the form

```
@tag[[arg0, arg1, arg2, ...]]
```

where the list of arguments may be omitted if the tag doesn't require it.

### Caveats

- There **must not** be any space between the `@` symbol and `tag` or between the `tag` and `[[`. 

- While the opening `[[` never appears in a valid C/C++ code (not sure about Fortran, someone can enlighten me), the closing `]]` can occur e.g. as in `x[y[i]]`.

- For now, as *grx* doesn't parse anything that's not part of its control structure, `@tag[[x[y]]]` appears to the system as

`@tag` `[[` first parameter `"x[y"` `]]` followed by the string `"]"`


- Likewise, commas could prove problematic, as `@tag[[f(x,y), z]]` appears as

`@tag` `[[` first parameter `"f(x"` `,` second parameter `"y)"` `,` third parameter `" z"` `]]`

- Both of these issues can be rectified also inspecting various kinds of brackets in the parameter list. This somewhat violates the "no knowledge of underlying language" principle, but may well be required for usability. (The alternative would be, for example, to use `~` or `$` instead of `,` or `[[`, but I think that is horrendous syntax)

### Array expansion

The only control directive which is not an `@tag` is the array expansion. This is best explained by an example. When writing a 3D code we end up writing `f[x3][x2][x1]` a lot. In 11D this becomes `f[x11][x10]...[x1]` which is even worse. In *grx*, we can instead write

```
f[[x#]]
```

The system would generate the correct multidim-array syntax for the corresponding language by iterating over `#`, specifically:

- In C, surround **each copy** of the inner string by `[...]` and replace the `#` by numbers in **descending** order.
- In Fortran, append a comma to **each copy** *apart from the last one*, run `#` in **ascending** order, then surround the **whole thing** by `(...)`

In general, any `[[...]]` which does **not** immediately follow an `@tag` is treated as an array expansion. Again the `#` may potentially collide with C preprocessor directives, but I hardly think that is a likely occurrence inside array indexes.

### Variables

At the end of the day, *grx* is a glorified macro substitution engine, and so it needs some sort of token in the text to be replaced by value of some variables. In grx, these tokens take the form

```
`var`
```

or if multiple variables are to be concatenated

```
`var_1`var_2`var_3`
```

In general, the system looks for strings between pairs of `` `...` `` and checks whether it matches a variable name. If not it will leave the whole thing alone, including the `` ` ``. At the time there is no way to generically define a variable in *grx*, but rather variables get defined in iteration structures (see `@iterate`)
