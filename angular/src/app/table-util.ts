export class PageEntry {
  page?: number;
  is_ellipse?: boolean = false;
  is_current?: boolean = false;
}

export class Pagination<T> {
  readonly itemsPerPageOptions = [10, 20, 50, 100, 200, 500];
  readonly _pageEntryPadding = 3;
  private _fieldComparators: { [key: string]: (a, b) => number } = {};
  private _searchMatcher: (item: T, key: string) => boolean;

  private _page: number;
  private _pages: number;
  private _itemsPerPage: number; // make sure use one of itemsPerPageOptions as the default value

  private _sortField: string;
  private _isSortDescending: boolean;
  private _searchKey: string;

  private _sourceItems: T[];
  private _items: T[];
  private _itemPages: T[][];
  private _pageItems: T[];
  private _pageEntries: PageEntry[];

  constructor(sourceItems?: T[], itemsPerPage: number = 20) {
    this._sourceItems = sourceItems;
    this._itemsPerPage = itemsPerPage;
    this.updatePages()
  }

  get pages(): number {
    return this._pages
  }

  get page(): number {
    return this._page
  }

  set page(page: number) {
    if (page !== this._page) {
      this._page = page;
      this.updatePage()
    }
  }

  get itemsPerPage(): number {
    return this._itemsPerPage
  }

  set itemsPerPage(itemsPerPage: number) {
    if (itemsPerPage !== this.itemsPerPage) {
      this._itemsPerPage = itemsPerPage;
      this.updatePages()
    }
  }

  get sourceItems(): T[] {
    return this._sourceItems
  }

  set sourceItems(items: T[]) {
    if (items !== this._sourceItems) {
      this._sourceItems = items;
      this.updatePages()
    }
  }

  get items(): T[] {
    return this._items;
  }

  get pageItems(): T[] {
    return this._pageItems;
  }

  get pageEntries(): PageEntry[] {
    return this._pageEntries;
  }

  get sortField(): string {
    return this._sortField
  }

  get isSortDescending(): boolean {
    return this._isSortDescending;
  }

  get startRow(): number { // start from 1
    return (this._page - 1) * this._itemsPerPage + 1
  }

  get endRow(): number { // start from 1, inclusive
    return (this._page - 1) * this._itemsPerPage + this._pageItems.length
  }

  reload() {
    this.updatePages()
  }

  private updatePages() {
    // no items or invalid itemsPerPage
    if (!this._sourceItems || !this._sourceItems.length || this._itemsPerPage <= 0) {
      this._items = [];
      this._itemPages = [[]];
      this._pages = 1;
      this._page = 1;
      this._pageItems = this._itemPages[0];
      this.makeEntries();
      return
    }

    let items = this._sourceItems;
    let usingSource = true;

    // do filtering if required
    if (this._searchMatcher && this._searchKey) {
      items = items.filter((item) => this._searchMatcher(item, this._searchKey));
      usingSource = false;
    }

    // do sorting if required
    if (this._sortField) {
      if (usingSource) {
        items = items.slice(); // make a copy first
        usingSource = false;
      }
      // find compare function
      const compareFn = this._fieldComparators[this._sortField];
      const sortFieldSegments = this._sortField.split('.');

      const startTime = new Date().getTime();
      items.sort((a, b) => {
        const fa = Pagination.extractField(a, sortFieldSegments);
        const fb = Pagination.extractField(b, sortFieldSegments);

        if (fa == undefined || fa == null) {
          return (fb == undefined || fb == null) ? 0 : 1;
        }
        if (fb == undefined || fb == null)
          return -1;

        const val = compareFn ? compareFn(fa, fb) : (fa < fb ? -1 : (fa > fb ? 1 : 0));
        if (this._isSortDescending)
          return -val;
        else
          return val
      });
      //console.info(new Date().getTime() - startTime)
    }
    this._items = items;

    // compute pages
    this._pages = Math.ceil(this._items.length / this._itemsPerPage) || 1; // at least 1 page
    this._page = 1;
    this._itemPages = [];
    for (let i = 0; i < this._pages; ++i) {
      this._itemPages.push(this._items.slice(i * this._itemsPerPage, (i + 1) * this._itemsPerPage))
    }

    // update current page
    this.updatePage();
  }

  private static extractField(obj: any, segments: string[]) {
    let ret = obj;
    for (let segment of segments) {
      if (typeof ret != 'object')
        return null;
      ret = ret[segment]
    }
    return ret;
  }

  private updatePage() {
    this.makeEntries();
    if (this._page < 1 || this._page > this._pages) {
      this._pageItems = [];
      return
    }
    this._pageItems = this._itemPages[this._page - 1];
  }

  private makeEntries() {
    const start = Math.max(1, this._page - this._pageEntryPadding);
    const end = Math.min(this._pages, this._page + this._pageEntryPadding);

    this._pageEntries = [];
    for (let i = start; i <= end; ++i) {
      let entry: PageEntry = {page: i};
      if (i == this._page)
        entry.is_current = true;
      this._pageEntries.push(entry)
    }
    if (start > 2) {
      this._pageEntries.unshift({is_ellipse: true})
    }
    if (start > 1) {
      this._pageEntries.unshift({page: 1})
    }
    if (end < this._pages - 1) {
      this._pageEntries.push({is_ellipse: true})
    }
    if (end < this._pages) {
      this._pageEntries.push({page: this._pages})
    }
  }

  nextPage() {
    if (this._page < this._pages) {
      this.page++;
    }
  }

  previousPage() {
    if (this._page > 1) {
      this.page--;
    }
  }

  firstPage() {
    this.page = 1
  }

  lastPage() {
    this.page = this._pages;
  }

  sort(field: string, isDescending: boolean = false) {
    if (field != this._sortField || isDescending != this._isSortDescending) {
      this._sortField = field;
      this._isSortDescending = isDescending;
      this.updatePages();
    }
  }

  search(key: string) {
    if (key != this._searchKey) {
      this._searchKey = key;
      this.updatePages()
    }
  }

  setSearchMatcher(matcher: (item: T, key: string) => boolean) {
    this._searchMatcher = matcher;
  }

  setFieldComparator(field: string, compareFn: (a, b) => number) {
    this._fieldComparators[field] = compareFn
  }

}

export function makeSortField<T>(pages: Pagination<T>): (field: string, th: HTMLElement) => any {
  return function (field: string, th: HTMLElement) {
    let sibling = th.parentNode.firstChild;
    while (sibling) {
      if (sibling.nodeType == 1 && sibling != th) {
        (sibling as Element).classList.remove('sorted', 'descending', 'ascending');
      }
      sibling = sibling.nextSibling;
    }

    if (!th.classList.contains('sorted')) {
      th.classList.add('sorted', 'ascending');
      th.classList.remove('descending');
      pages.sort(field, false);
    } else {
      if (th.classList.contains('ascending')) {
        th.classList.remove('ascending');
        th.classList.add('descending');
        pages.sort(field, true);
      } else {
        th.classList.remove('sorted', 'descending', 'ascending');
        pages.sort(null);
      }
    }
  }
}
