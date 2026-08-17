---
name: open-source-fixer
description: >
  Check that the repository has minimal criteria for open sourcing for Nav
---

# Open Source fixer

This skill ensures that the repository has the minimum requirements to be open sourced in Nav according to [Krav til åpne repo under github.com/navikt](https://github.com/navikt/offentlig?tab=readme-ov-file#krav-til-%C3%A5pne-repo-under-githubcomnavikt)

Do not check git history. This skill skill only ensures that the needed files are in place.

The app repository shall have these files on the root folder:
* `.github/CODEOWNERS`
* `LICENSE.md`
* `README.md`

## CODEOWNERS

This file shall have this content:

```
* @navikt/teamdokumenthandtering
```

## LICENSE.md

This file shall have this content:

```
# The MIT License

Copyright <YEAR> Nav (Arbeids- og velferdsdirektoratet) - The Norwegian Labour and Welfare Administration

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
USE OR OTHER DEALINGS IN THE SOFTWARE.
```

`<YEAR>` is set to the current year. If this file already exists, there is no need to change the year.

## README.md

This file shall have the following disposition.
Content in existing README shall be moved to the relevant section.
Let the user review this.

Any links pointing to confluence.adeo.no or intern.dev.nav.no shall be suffixed with (Nav-internt).
Example: [Swagger (Nav-internt)](https://dokdok.intern.dev.nav.no/swagger-ui.html)

````markdown
# Navn på appen

Beskrivelse av hva appen som lages i dette repositoryet gjør.

## Komme i gang

Kjør tester og bygg appen

```
mvn clean verify
```

---

## Henvendelser

Lag en issue i repository.

### For Nav-ansatte

Spørsmål om appen kan stilles på [#team_dokumentløsninger](https://nav-it.slack.com/archives/C6W9E5GPJ)

## Lisens

[MIT](LICENSE.md)
````
